import asyncio
import shlex
import uuid

import grpc
from typing import Callable

from src.gen import stockalerter_pb2
from src.gen import stockalerter_pb2_grpc


class StockAlerterClient:
    def __init__(self, server_address: str, log_output: Callable[[str], None]):
        self.server_address = server_address
        self.log_output = log_output
        self.connected = False
        self.connect_lock = asyncio.Lock()

    async def connect(self):
        async with self.connect_lock:
            try:
                self.log_output(f"Connecting to server at {self.server_address}...\n")
                await asyncio.sleep(5)

                self.connected = True
                self.log_output("Connected to server.\n")

            except asyncio.CancelledError as e:
                self.log_output(f"Connection cancelled: {e}\n")

    async def close(self):
        self.log_output("Waiting for connection to close ...")
        async with self.connect_lock:
            self.log_output("Closing client ...\n")
            await asyncio.sleep(5)

            self.connected = False
            self.log_output("Client closed.")

    async def handle_command(self, command: str):
        """
        Handle a command from the input field.
        This function is called when the user presses Enter.
        """
        if not self.connected:
            self.log_output("Not connected to server.\n")
            return

        self.log_output(f"Command received: {command}\n")
