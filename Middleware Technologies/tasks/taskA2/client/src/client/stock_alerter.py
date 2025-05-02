import asyncio
import shlex
import uuid

import grpc
from typing import Callable

from src.gen import stockalerter_pb2
from src.gen import stockalerter_pb2_grpc

# types
type Money = tuple[str, int, int]  # (units, nanos)


# helper functions
def convert_str_to_money(price_str: str) -> Money:
    """
    Convert a string price to a Money tuple.
    The string can be in the format "123.456" or "123" or "123.000000456".
    Currently, only USD.
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
    return "USD", units, nanos


def convert_money_to_str(money: Money) -> str:
    """
    Convert a Money tuple to a string.
    Currently, only USD (not displaying currency code).
    """
    _, units, nanos = money
    if nanos == 0:
        return str(units)
    elif nanos < 10 ** 9:
        units_str = str(units)
        nanos_str = str(nanos).rstrip("0")  # remove trailing zeros
        return f"{units_str}.{nanos_str}"
    else:
        raise ValueError("Invalid Money format")


def format_notification(notification: stockalerter_pb2.NotificationMessage) -> str:
    """Format a notification message for display."""
    alert_type = stockalerter_pb2.AlertType.Name(notification.alert_type)
    alert_message = notification.alert_message
    timestamp = notification.timestamp.ToDatetime().strftime("%Y-%m-%d %H:%M:%S")
    return f"[{timestamp}][{alert_type}] {alert_message}"


class StockAlerterClient:
    def __init__(self, server_address: str, log_output: Callable[[str], None]):
        self.server_address = server_address
        self.log_output = log_output
        self.connected = False
        self.connect_lock = asyncio.Lock()
        self.grpc_channel: grpc.aio.Channel | None = None
        self.grpc_stub: stockalerter_pb2_grpc.StockAlerterStub | None = None
        # key: stock_symbol, value: {"id": subscription_id, "task": asyncio_task, "stream": notification_stream}
        self.subscriptions = {}
        self.subscriptions_lock = asyncio.Lock()

    async def connect(self):
        """Connect to the server."""
        async with self.connect_lock:
            try:
                self.log_output(f"Connecting to server at {self.server_address}...\n")

                # create channel with keepalive options
                grpc_channel = grpc.aio.insecure_channel(
                    self.server_address,
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
                self.grpc_channel = grpc_channel
                self.grpc_stub = stockalerter_pb2_grpc.StockAlerterStub(grpc_channel)

                self.connected = True
                self.log_output("Connected to server.\n")

            except asyncio.CancelledError as e:
                self.log_output(f"Connection cancelled: {e}\n")
            except asyncio.TimeoutError:
                self.log_output("Connection timed out.\n")
            except grpc.aio.AioRpcError as e:
                self.log_output(f"gRPC error: {e.code()} - {e.details()}\n")
            except Exception as e:
                self.log_output(f"Unexpected error: {e}\n")

    async def close(self):
        """Close the connection to the server and clean up resources."""
        self.log_output("Waiting for connection to close ...")
        async with self.connect_lock:
            self.log_output("Closing client ...\n")

            async with self.subscriptions_lock:
                subscriptions_keys = list(self.subscriptions.keys())
            for stock_symbol in subscriptions_keys:
                await self.handle_unsubscribe(stock_symbol)

            async with self.subscriptions_lock:
                if self.subscriptions:
                    self.log_output(f"Error: {len(self.subscriptions)} subscriptions still active.\n")

            if self.grpc_channel is not None:
                await self.grpc_channel.close()
            self.grpc_channel = None
            self.grpc_stub = None

            self.connected = False
            self.log_output("Client closed.\n")

    async def handle_subscribe(self, stock_symbol: str, above: Money | None, below: Money | None):
        """Handle a subscription request."""
        self.log_output(f"[{stock_symbol}] Subscribing (above: {above}, below: {below})...\n")

        if not self.connected:
            self.log_output("Not connected to server.\n")
            return

        async with self.subscriptions_lock:
            if stock_symbol in self.subscriptions:
                self.log_output(f"[{stock_symbol}] Already subscribed.\n")
                return

            subscription_id = f"{stock_symbol}-{uuid.uuid4()}"
            notify_above_price = None
            notify_below_price = None
            if above is not None:
                notify_above_price = stockalerter_pb2.Money(
                    currency_code=above[0], units=above[1], nanos=above[2]
                )
            if below is not None:
                notify_below_price = stockalerter_pb2.Money(
                    currency_code=below[0], units=below[1], nanos=below[2]
                )
            subscription_request = stockalerter_pb2.SubscriptionRequest(
                subscription_id=subscription_id,
                stock_symbol=stock_symbol,
                notify_above_price=notify_above_price,
                notify_below_price=notify_below_price,
            )

            try:
                notification_stream = self.grpc_stub.Subscribe(subscription_request)
                subscription_task = asyncio.create_task(self._handle_subscription_stream(stock_symbol))
                self.subscriptions[stock_symbol] = {
                    "id": subscription_id,
                    "task": subscription_task,
                    "stream": notification_stream,
                }
                self.log_output(f"[{stock_symbol}] Subscribed with ID: {subscription_id}\n")

            except grpc.aio.AioRpcError as e:
                self.log_output(f"gRPC error: {e.code()} - {e.details()}\n")
            except Exception as e:
                self.log_output(f"Unexpected error: {e}\n")

    async def handle_unsubscribe(self, stock_symbol: str):
        """Handle an unsubscription request."""
        self.log_output(f"[{stock_symbol}] Unsubscribing...\n")
        subscription_task: asyncio.Task | None = None

        async with self.subscriptions_lock:
            if stock_symbol not in self.subscriptions:
                self.log_output(f"[{stock_symbol}] Not subscribed.\n")
                return

            subscription = self.subscriptions[stock_symbol]
            subscription_task = subscription["task"]
            subscription_task.cancel()
            self.log_output(f"[{stock_symbol}] Cancellation requested for task.\n")

        if subscription_task is not None:
            try:
                await subscription_task
                self.log_output(f"[{stock_symbol}] Subscription task finished normally after cancel request.\n")
            except asyncio.CancelledError:
                self.log_output(f"[{stock_symbol}] Subscription task acknowledged cancellation.\n")
            except Exception as e:
                self.log_output(f"[{stock_symbol}] Error waiting for subscription task completion: {e}\n")

    async def _handle_subscription_stream(self, stock_symbol: str):
        """
        Handle a subscription stream request.
        Should be created as a separate task.
        """
        self.log_output(f"[{stock_symbol}] Listening for notifications...\n")
        notification_stream: grpc.aio.StreamStreamCall | None = None

        async with self.subscriptions_lock:
            if stock_symbol not in self.subscriptions:
                self.log_output(f"[{stock_symbol}] Subscription disappeared before task could get stream.\n")
                return

            notification_stream = self.subscriptions[stock_symbol]["stream"]

        if notification_stream is None:
            self.log_output(f"[{stock_symbol}] No notification stream found. Exiting task.\n")
            return

        try:
            self.log_output(f"[{stock_symbol}] Listening for notifications...\n")
            async for notification in notification_stream:
                notification_str = format_notification(notification)
                self.log_output(f"[{stock_symbol}] Notification: {notification_str}\n")
            self.log_output(f"[{stock_symbol}] Notification stream ended normally.\n")
        except grpc.aio.AioRpcError as e:
            if e.code() == grpc.StatusCode.CANCELLED:
                self.log_output(f"[{stock_symbol}] Notification stream cancelled (gRPC code: {e.code()}).\n")
            else:
                self.log_output(f"[{stock_symbol}] gRPC error while listening: {e.code()} - {e.details()}\n")
        except Exception as e:
            self.log_output(f"[{stock_symbol}] Unexpected error: {e}\n")
        finally:
            self.log_output(f"[{stock_symbol}] Cleanup...\n")
            async with self.subscriptions_lock:
                if stock_symbol in self.subscriptions:
                    subscription = self.subscriptions.pop(stock_symbol)
                    self.log_output(f"[{stock_symbol}] Cleaned up subscription entry: {subscription['id']}\n")
                else:
                    self.log_output(f"[{stock_symbol}] Subscription entry already removed when task tried cleanup.\n")
            self.log_output(f"[{stock_symbol}] Subscription task finished.\n")

    async def _handle_sub_command(self, args: list[str], unknown_cmd_msg: str):
        match args:
            case [stock_symbol]:
                await self.handle_subscribe(stock_symbol, None, None)
            case [stock_symbol, "above", price]:
                try:
                    price = convert_str_to_money(price)
                except ValueError as e:
                    self.log_output(f"Error converting price: {e}\n")
                    return
                await self.handle_subscribe(stock_symbol, price, None)
            case [stock_symbol, "below", price]:
                try:
                    price = convert_str_to_money(price)
                except ValueError as e:
                    self.log_output(f"Error converting price: {e}\n")
                    return
                await self.handle_subscribe(stock_symbol, None, price)
            case [stock_symbol, "above", price_above, "below", price_below]:
                try:
                    price_above = convert_str_to_money(price_above)
                    price_below = convert_str_to_money(price_below)
                except ValueError as e:
                    self.log_output(f"Error converting price: {e}\n")
                    return
                await self.handle_subscribe(stock_symbol, price_above, price_below)
            case _:
                self.log_output(unknown_cmd_msg)

    async def _handle_unsub_command(self, args: list[str], unknown_cmd_msg: str):
        match args:
            case [stock_symbol]:
                await self.handle_unsubscribe(stock_symbol)
            case _:
                self.log_output(unknown_cmd_msg)

    async def handle_command(self, command_str: str):
        """
        Handle a command from the input field.
        This function is called when the user presses Enter.
        """
        if not command_str:
            return

        if not self.connected:
            self.log_output("Not connected to server.\n")
            return

        try:
            cmd_parts = shlex.split(command_str)
        except ValueError as e:
            self.log_output(f"Error parsing command: {e}\n")
            return

        cmd, *args = cmd_parts
        unknown_cmd_msg = (
            f"Unknown command: {shlex.join([cmd] + args)}\n"
            "  sub <stock_symbol> [above <price>] [below <price>]\n"
            "  unsub <stock_symbol>\n"
        )
        if cmd == "sub":
            await self._handle_sub_command(args, unknown_cmd_msg)
        elif cmd == "unsub":
            await self._handle_unsub_command(args, unknown_cmd_msg)
        else:
            self.log_output(unknown_cmd_msg)
