package server;

import gen.*;
import io.grpc.stub.StreamObserver;

import java.util.Collections;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.protobuf.Timestamp;

import java.time.Instant;

// Extend the generated base class for the service
public class StockAlerterImpl extends StockAlerterGrpc.StockAlerterImplBase {

    private static final Logger logger = Logger.getLogger(StockAlerterImpl.class.getName());

    // Store active client observers (subscriptions)
    // Key: subscriptionId, Value: StreamObserver for the client
    // Use ConcurrentHashMap for thread safety
    private final ConcurrentHashMap<String, StreamObserver<NotificationMessage>> subscribers = new ConcurrentHashMap<>();

    // --- Implement the 'subscribe' RPC (Server Streaming) ---
    @Override
    public void subscribe(SubscriptionRequest request, StreamObserver<NotificationMessage> responseObserver) {
        String subscriptionId = request.getSubscriptionId();
        String stockSymbol = request.getStockSymbol();
        logger.info("Received subscription request: ID=" + subscriptionId + ", Symbol=" + stockSymbol);

        // TODO: Add logic to validate the request (e.g., check if stock symbol exists)

        // Store the observer for this subscriber
        // If a subscription with the same ID already exists, it will be replaced (update subscription)
        subscribers.put(subscriptionId, responseObserver);
        logger.info("Client subscribed: " + subscriptionId);

        // Optional: Send an initial confirmation message
        try {
            Timestamp timestamp = Timestamp.newBuilder().setSeconds(Instant.now().getEpochSecond()).build();
            NotificationMessage confirmation = NotificationMessage.newBuilder()
                    .setStockSymbol(stockSymbol)
                    .setAlertType(AlertType.GENERAL_UPDATE)
                    .setAlertMessage("Subscription confirmed for " + stockSymbol)
                    .setTimestamp(timestamp)
                    .build();
            responseObserver.onNext(confirmation);
        } catch (Exception e) {
            logger.log(Level.WARNING, "Error sending confirmation to " + subscriptionId, e);
            subscribers.remove(subscriptionId); // Clean up if sending failed immediately
        }


        // --- IMPORTANT ---
        // Keep the connection open for streaming. DO NOT call responseObserver.onCompleted() here.
        // You will call responseObserver.onNext() later when you have stock updates to send.
        // You need a separate mechanism (e.g., a background thread, message queue listener)
        // to monitor stock prices and push updates to the relevant observers in the 'subscribers' map.

        // Handle client disconnection: gRPC might provide mechanisms, or you might need custom handling
        // For example, using ServerCallStreamObserver if more control over the stream is needed.
        // ((io.grpc.stub.ServerCallStreamObserver<NotificationMessage>) responseObserver).setOnCancelHandler(() -> {
        //     logger.info("Client disconnected: " + subscriptionId);
        //     subscribers.remove(subscriptionId);
        // });
    }

    // --- Implement the 'unsubscribe' RPC (Unary) ---
    @Override
    public void unsubscribe(UnsubscribeRequest request, StreamObserver<UnsubscribeResponse> responseObserver) {
        String subscriptionId = request.getSubscriptionId();
        logger.info("Received unsubscribe request: ID=" + subscriptionId);

        // Remove the subscriber
        StreamObserver<NotificationMessage> observer = subscribers.remove(subscriptionId);

        String message;
        if (observer != null) {
            message = "Successfully unsubscribed: " + subscriptionId;
            logger.info(message);
            try {
                // Optionally notify the client stream that it's completed from the server side
                observer.onCompleted();
            } catch (Exception e) {
                // Log error if observer is already closed/cancelled
                logger.log(Level.FINE, "Observer already closed for " + subscriptionId, e);
            }
        } else {
            message = "Subscription ID not found: " + subscriptionId;
            logger.warning(message);
        }

        // Send confirmation back to the client
        UnsubscribeResponse response = UnsubscribeResponse.newBuilder()
                .setConfirmationMessage(message)
                .build();
        responseObserver.onNext(response);
        responseObserver.onCompleted();
    }

    // --- Method to be called by your stock update mechanism ---
    public void sendStockUpdate(NotificationMessage notification) {
        String targetSymbol = notification.getStockSymbol();
        logger.info("Attempting to send update for symbol: " + targetSymbol);

        // Iterate over subscribers and send to those interested in this stock symbol
        // NOTE: This is a basic approach. For efficiency, you might map stock symbols
        // directly to lists of observers rather than iterating through all subscribers.
        subscribers.forEach((subscriptionId, observer) -> {
            // TODO: Add logic here to check if this subscriber's request matches the notification
            // (e.g., check stock symbol, price thresholds from the original SubscriptionRequest)
            // For now, we assume any subscriber might be interested (needs refinement)

            logger.fine("Sending update to subscriber: " + subscriptionId);
            try {
                observer.onNext(notification);
            } catch (Exception e) {
                // Handle potential errors (e.g., client disconnected)
                logger.log(Level.WARNING, "Error sending update to " + subscriptionId + ". Removing subscriber.", e);
                // Remove the observer if sending fails (likely disconnected)
                subscribers.remove(subscriptionId);
            }
        });
    }
}