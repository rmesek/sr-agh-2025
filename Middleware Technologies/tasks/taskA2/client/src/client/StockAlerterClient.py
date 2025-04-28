import grpc
import logging
import time
import threading
import uuid

# Import generated code - Adjust path relative to src
# Assumes you run the client from the root directory or have src in PYTHONPATH
from src.gen import stockalerter_pb2
from src.gen import stockalerter_pb2_grpc

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_money(units: int, nanos: int = 0, currency_code: str = "USD") -> stockalerter_pb2.Money:
    """Helper function to create a Money message."""
    return stockalerter_pb2.Money(currency_code=currency_code, units=units, nanos=nanos)

def listen_for_notifications(stub, subscription_id):
    """Handles incoming notification messages in a separate thread."""
    logging.info(f"[{subscription_id}] Listener thread started.")
    try:
        # Create a sample subscription request
        # In a real app, get these details from the user
        request = stockalerter_pb2.SubscriptionRequest(
            subscription_id=subscription_id,
            stock_symbol="AAPL", # Example stock
            notify_above_price=create_money(180), # Notify if price > 180 USD
            notify_below_price=create_money(170)  # Notify if price < 170 USD
        )
        logging.info(f"[{subscription_id}] Sending subscription request: {request.stock_symbol}")

        # Call the Subscribe RPC. This returns an iterator.
        notifications = stub.Subscribe(request)

        # Iterate over the stream of notifications from the server
        for notification in notifications:
            timestamp_str = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(notification.timestamp.seconds))
            price = notification.current_price.units + notification.current_price.nanos / 1e9
            logging.info(
                f"[{subscription_id}] Received Notification:\n"
                f"  Symbol: {notification.stock_symbol}\n"
                f"  Price: {notification.current_price.currency_code} {price:.2f}\n"
                f"  Alert Type: {stockalerter_pb2.AlertType.Name(notification.alert_type)}\n"
                f"  Message: '{notification.alert_message}'\n"
                f"  Related: {list(notification.related_symbols)}\n"
                f"  Timestamp: {timestamp_str} ({notification.timestamp.seconds})"
            )
            # Add logic here to react to specific alert types if needed

    except grpc.RpcError as e:
        # Handle different types of errors
        if e.code() == grpc.StatusCode.CANCELLED:
            logging.warning(f"[{subscription_id}] Subscription stream cancelled (likely server shutdown or unsubscribe).")
        elif e.code() == grpc.StatusCode.UNAVAILABLE:
             logging.error(f"[{subscription_id}] Connection error: Server unavailable. Details: {e.details()}")
             # Implement retry logic here if desired
        else:
            logging.error(f"[{subscription_id}] An RPC error occurred: {e.code()} - {e.details()}")
    except Exception as e:
        logging.error(f"[{subscription_id}] Listener thread encountered an error: {e}", exc_info=True)
    finally:
        logging.info(f"[{subscription_id}] Listener thread finished.")


def run_client(server_address='localhost:50051'):
    """Runs the gRPC client."""
    # Create a secure or insecure channel
    # Use grpc.secure_channel for production with credentials
    channel = grpc.insecure_channel(server_address)
    stub = stockalerter_pb2_grpc.StockAlerterStub(channel)

    # Generate a unique ID for this client session/subscription
    subscription_id = f"client-{uuid.uuid4()}"
    logging.info(f"Client started with subscription ID: {subscription_id}")

    listener_thread = None
    try:
        # Start listening in a background thread
        listener_thread = threading.Thread(target=listen_for_notifications, args=(stub, subscription_id), daemon=True)
        listener_thread.start()

        # Keep the main thread alive, waiting for user input to unsubscribe or exit
        while True:
            action = input("Enter 'u' to unsubscribe, 'q' to quit: ").strip().lower()
            if action == 'u':
                logging.info(f"[{subscription_id}] Sending unsubscribe request...")
                try:
                    unsubscribe_request = stockalerter_pb2.UnsubscribeRequest(subscription_id=subscription_id)
                    response = stub.Unsubscribe(unsubscribe_request)
                    logging.info(f"[{subscription_id}] Unsubscribe response: {response.confirmation_message}")
                    # The listener thread should receive a CANCELLED status and exit
                    break # Exit loop after unsubscribing
                except grpc.RpcError as e:
                    logging.error(f"[{subscription_id}] Failed to unsubscribe: {e.code()} - {e.details()}")
                except Exception as e:
                     logging.error(f"[{subscription_id}] Error during unsubscribe: {e}", exc_info=True)

            elif action == 'q':
                logging.info("Quitting...")
                break
            else:
                logging.warning("Invalid input. Enter 'u' or 'q'.")

    except KeyboardInterrupt:
        logging.info("Client interrupted. Shutting down.")
    finally:
        # Cleanly close the channel and wait for the listener thread
        if listener_thread and listener_thread.is_alive():
             logging.info("Waiting for listener thread to finish...")
             # Note: If unsubscribe wasn't called, the listener might block
             # waiting for the server. Closing the channel might cause it
             # to raise an error and terminate.
             channel.close()
             listener_thread.join(timeout=5) # Wait max 5 seconds
             if listener_thread.is_alive():
                 logging.warning("Listener thread did not terminate gracefully.")
        else:
             channel.close() # Close channel if listener wasn't started or already finished
        logging.info("Client shutdown complete.")


if __name__ == '__main__':
    run_client() # Use default server address
    # Example: run_client(server_address='192.168.1.100:50051')