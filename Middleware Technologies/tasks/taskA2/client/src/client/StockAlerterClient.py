import asyncio
import shlex
import uuid

import grpc
from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.widgets import TextArea

from src.gen import stockalerter_pb2
from src.gen import stockalerter_pb2_grpc

# types
type Money = tuple[int, int]  # (units, nanos)

# global variables
DEFAULT_SERVER_ADDRESS = "localhost:50051"
# key: stock_symbol, value: {"id": subscription_id, "task": asyncio_task, "stream": notification_stream}
subscriptions = {}
subscriptions_lock = asyncio.Lock()
grpc_channel: grpc.aio.Channel | None = None
grpc_stub: stockalerter_pb2_grpc.StockAlerterStub | None = None

# output Area
output_field = TextArea(multiline=False, wrap_lines=True)


def log_output(text: str):
    """
    Write text to the output field.
    """
    output_field.buffer.insert_text(text)
    # output_field.buffer.cursor_position = len(output_field.buffer.text)


# input Area
def input_accepted(buff: Buffer) -> bool:
    """
    Accept handler for the input buffer.
    Takes the text from the input buffer, appends it to the output_field,
    and then clears the input buffer.
    """
    input_text = buff.text
    asyncio.create_task(handle_command(input_text))
    buff.reset()
    return True


input_field = TextArea(
    height=1,
    prompt="> ",
    multiline=False,
    wrap_lines=False,
    # call this function on Enter
    accept_handler=input_accepted,
)

# layout
container = HSplit(
    [
        # top pane for output
        Window(
            content=BufferControl(buffer=output_field.buffer), always_hide_cursor=True
        ),
        # separator line
        Window(height=1, char="─", style="class:line"),
        # bottom pane for input
        input_field,
    ]
)

kb = KeyBindings()  # Ctrl+C and Ctrl+Q


@kb.add("c-c", eager=True)
@kb.add("c-q", eager=True)
def _(event):
    """
    Handle Ctrl+C or Ctrl+Q to exit the application.
    """
    event.app.exit()


# create the main Application instance
application = Application(
    layout=Layout(container, focused_element=input_field),
    key_bindings=kb,
    full_screen=True,  # or False?
)


async def print_hello():
    # TODO: Remove this function
    """
    An asynchronous task that runs in the background.
    It appends "Hello World" to the output field's buffer every few seconds.
    """
    try:
        while True:
            log_output("Hello World\n")
            await asyncio.sleep(5)
    except asyncio.CancelledError:
        pass  # expected, the task was cancelled
    except Exception as e:
        # log other potential errors
        log_output("Error in print_hello: {e}\n")


def convert_str_to_money(price_str: str) -> Money:
    """
    Convert a string price to a Money tuple.
    """
    price_parts = price_str.strip().split(".")
    if len(price_parts) > 2:
        raise ValueError("Invalid price format")
    units = price_parts[0]
    nanos = price_parts[1] if len(price_parts) == 2 else "0"
    if len(nanos) > 9:
        raise ValueError("Nanos part exceeds 9 digits")
    nanos = nanos.ljust(9, "0")  # ensure nanos is 9 digits
    units = int(units)
    nanos = int(nanos)
    return units, nanos


def convert_money_to_str(money: Money) -> str:
    """
    Convert a Money tuple to a string.
    """
    units, nanos = money
    if nanos == 0:
        return str(units)
    elif nanos < 10**9:
        units_str = str(units)
        nanos_str = str(nanos).rstrip("0")  # remove trailing zeros
        return f"{units_str}.{nanos_str}"
    else:
        raise ValueError("Invalid Money format")


async def handle_command(command_str: str):
    """
    Handle commands submitted by the user.
    """
    try:
        cmd_parts = shlex.split(command_str)
    except ValueError as e:
        log_output(f"Error parsing command: {e}\n")
        return

    cmd, *args = cmd_parts
    unknown_cmd_msg = (
        f"Unknown command: {shlex.join([cmd] + args)}\n"
        "  sub <stock_symbol> [above <price>] [below <price>]\n"
        "  unsub <stock_symbol>\n"
    )
    if cmd == "sub":
        match args:
            case [stock_symbol]:
                log_output(f"Subscribing to {stock_symbol}\n")
                await handle_subscribe(stock_symbol, None, None)
            case [stock_symbol, "above", price]:
                log_output(f"Subscribing to {stock_symbol} above {price}\n")
                try:
                    price = convert_str_to_money(price)
                except ValueError as e:
                    log_output(f"Error converting price: {e}\n")
                    return
                await handle_subscribe(stock_symbol, price, None)
            case [stock_symbol, "below", price]:
                log_output(f"Subscribing to {stock_symbol} below {price}\n")
                try:
                    price = convert_str_to_money(price)
                except ValueError as e:
                    log_output(f"Error converting price: {e}\n")
                    return
                await handle_subscribe(stock_symbol, None, price)
            case [stock_symbol, "above", price_above, "below", price_below]:
                log_output(
                    f"Subscribing to {stock_symbol} above {price_above} and below {price_below}\n"
                )
                try:
                    price_above = convert_str_to_money(price_above)
                    price_below = convert_str_to_money(price_below)
                except ValueError as e:
                    log_output(f"Error converting price: {e}\n")
                    return
                await handle_subscribe(stock_symbol, price_above, price_below)
            case _:
                log_output(unknown_cmd_msg)
    elif cmd == "unsub":
        match args:
            case [stock_symbol]:
                log_output(f"Unsubscribing from {stock_symbol}\n")
                await handle_unsubscribe(stock_symbol)
            case _:
                log_output(unknown_cmd_msg)
    else:
        log_output(unknown_cmd_msg)


async def monitor_notifications(stock_symbol: str):
    # TODO: Check if correct
    global grpc_channel, grpc_stub, subscriptions, subscriptions_lock

    if stock_symbol not in subscriptions:
        log_output(f"Not subscribed to {stock_symbol}. Cannot monitor notifications.\n")
        return

    sub_info = subscriptions[stock_symbol]
    log_output(f"Monitoring notifications for {stock_symbol}...\n")

    try:
        async for notification in sub_info["stream"]:
            timestamp_str = "N/A"
            if notification.HasField("timestamp"):
                ts = notification.timestamp.ToDatetime()
                timestamp_str = ts.strftime("%Y-%m-%d %H:%M:%S")

            price_str = "N/A"
            if notification.HasField("current_price"):
                price_str = convert_money_to_str(
                    (notification.current_price.units, notification.current_price.nanos)
                )

            alert_type_str = stockalerter_pb2.AlertType.Name(notification.alert_type)

            related_str = ""
            if notification.related_symbols:
                related_str = f" Related: [{', '.join(notification.related_symbols)}]"

            log_output(
                f"[{stock_symbol} @ {timestamp_str}] {alert_type_str}: "
                f"{notification.alert_message} (Price: {price_str}){related_str}\n"
            )
        log_output(f"[{stock_symbol}] Notification stream ended ({sub_info['id']}).\n")

    except grpc.aio.AioRpcError as e:
        log_output(
            f"[{stock_symbol}] Notification stream error: {e.code()} - {e.details()}\n"
        )
    except Exception as e:
        log_output(f"[{stock_symbol}] Unexpected error during monitoring: {e}\n")
    finally:
        log_output(f"[{stock_symbol}] Stopping monitoring...\n")
        if stock_symbol in subscriptions:
            removed_sub = subscriptions.pop(stock_symbol)
            log_output(f"[{stock_symbol}] Unsubscribed ({removed_sub['id']}).\n")
        else:
            log_output(f"[{stock_symbol}] Subscription already removed.\n")


async def handle_subscribe(stock_symbol: str, above: Money | None, below: Money | None):
    # TODO: Check if correct
    global grpc_channel, grpc_stub, subscriptions, subscriptions_lock

    if not grpc_stub:
        log_output("gRPC stub is not initialized. Cannot subscribe.\n")
        return

    log_output(f"Subscribing to {stock_symbol}...\n")
    async with subscriptions_lock:
        if stock_symbol in subscriptions:
            log_output(f"Already subscribed to {stock_symbol}. Unsubscribe first.\n")
            return

        subscription_id = f"{stock_symbol}-{uuid.uuid4()}"
        notify_above_price = (
            stockalerter_pb2.Money(currency_code="USD", units=above[0], nanos=above[1])
            if above
            else None
        )
        notify_below_price = (
            stockalerter_pb2.Money(currency_code="USD", units=below[0], nanos=below[1])
            if below
            else None
        )
        request = stockalerter_pb2.SubscriptionRequest(
            subscription_id=subscription_id,
            stock_symbol=stock_symbol,
            notify_above_price=notify_above_price,
            notify_below_price=notify_below_price,
        )
        log_output(
            f"Attempting subscribe: Symbol= {stock_symbol}, Above: {above}, Below: {below}\n"
        )
        try:
            notification_stream = grpc_stub.Subscribe(request)
            monitor_task = asyncio.create_task(monitor_notifications(stock_symbol))
            subscriptions[stock_symbol] = {
                "id": subscription_id,
                "task": monitor_task,
                "stream": notification_stream,
            }
            log_output(f"Subscribed to {stock_symbol} ({subscription_id}).\n")

        except grpc.aio.AioRpcError as e:
            log_output(
                f"Failed to subscribe to {stock_symbol}: {e.code()} - {e.details()}\n"
            )
        except Exception as e:
            log_output(f"An unexpected error occurred while subscribing: {e}\n")


async def handle_unsubscribe(stock_symbol: str):
    # TODO: Check if correct
    global grpc_channel, grpc_stub, subscriptions, subscriptions_lock

    log_output(f"Unsubscribing from {stock_symbol}...\n")
    async with subscriptions_lock:
        if stock_symbol not in subscriptions:
            log_output(f"Not subscribed to {stock_symbol}. Cannot unsubscribe.\n")
            return

        subscriptions[stock_symbol]["task"].cancel()
        try:
            await subscriptions[stock_symbol]["task"]
        except asyncio.CancelledError:
            pass  # expected, the task was cancelled
        except Exception as e:
            log_output(f"Error while unsubscribing: {e}\n")
        finally:
            subscriptions.pop(stock_symbol, None)


async def start_client(server_address: str):
    global grpc_channel, grpc_stub, subscriptions, subscriptions_lock

    log_output(f"Connecting to server at {server_address}...\n")
    try:
        # create channel with keepalive options
        grpc_channel = grpc.aio.insecure_channel(
            server_address,
            # options=[
            #     ('grpc.keepalive_time_ms', 10000),  # Send keepalive every 10s
            #     ('grpc.keepalive_timeout_ms', 5000),  # Wait 5s for pong ack
            #     ('grpc.keepalive_permit_without_calls', True),  # Allow keepalive pings when there are no calls
            #     ('grpc.http2.max_pings_without_data', 0),  # Allow infinite pings without data
            #     ('grpc.http2.min_time_between_pings_ms', 10000),  # Allow pings every 10s
            #     ('grpc.http2.min_ping_interval_without_data_ms', 5000),  # Allow pings when idle every 5s
            # ]
        )
        await asyncio.wait_for(grpc_channel.channel_ready(), timeout=5.0)
        grpc_stub = stockalerter_pb2_grpc.StockAlerterStub(grpc_channel)
        log_output("Connected to the server.\n")
    except asyncio.TimeoutError:
        log_output("Connection timed out.\n")
    except grpc.aio.AioRpcError as e:
        log_output(f"Failed to connect to server: {e.code()} - {e.details()}\n")
    except Exception as e:
        log_output(f"An unexpected error occurred: {e}\n")


async def stop_client():
    # TODO: Implement
    global grpc_channel, grpc_stub, subscriptions, subscriptions_lock

    log_output("Stopping client...\n")
    symbols_to_unsubscribe = []
    async with subscriptions_lock:
        symbols_to_unsubscribe = list(subscriptions.keys())

    for stock_symbol in symbols_to_unsubscribe:
        await handle_unsubscribe(stock_symbol)

    if grpc_channel is not None:
        await grpc_channel.close()
        grpc_channel = None
    grpc_stub = None
    subscriptions.clear()
    log_output("Client stopped.\n")


async def main():
    """
    The main entry point for the asynchronous application.
    It creates the background task and runs the prompt_toolkit application.
    """
    asyncio.create_task(start_client(DEFAULT_SERVER_ADDRESS))
    # asyncio.create_task(print_hello())

    log_output("Press Ctrl+C or Ctrl+Q to exit.\n")
    await application.run_async()
    print("Exiting application...")
    await stop_client()
    print("Application exited.")


if __name__ == "__main__":
    asyncio.run(main())
