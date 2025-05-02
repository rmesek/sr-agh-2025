import asyncio

from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import HSplit, Window, BufferControl, Layout
from prompt_toolkit.widgets import TextArea

from src.client.stock_alerter import StockAlerterClient

DEFAULT_SERVER_ADDRESS = "localhost:50051"


class StockAlerterTUI:
    def __init__(self, server_address: str):
        self.server_address = server_address
        self.client: StockAlerterClient | None = None

        # TUI components
        self.output_field = TextArea(multiline=False, wrap_lines=True)
        self.input_field = TextArea(
            height=1,
            prompt="> ",
            multiline=False,
            wrap_lines=False,
            # call this function on Enter
            accept_handler=self._handle_input,
        )
        # TUI layout
        container = HSplit(
            [
                # top pane for output
                Window(
                    content=BufferControl(buffer=self.output_field.buffer),
                    always_hide_cursor=True,
                ),
                # separator line
                Window(height=1, char="─", style="class:line"),
                # bottom pane for input
                self.input_field,
            ]
        )
        # TUI keybinds
        self.key_bindings = KeyBindings()

        @self.key_bindings.add("c-c", eager=True)
        @self.key_bindings.add("c-q", eager=True)
        def _(event):
            """Handle Ctrl+C or Ctrl+Q to exit the application."""
            event.app.exit()

        # TUI application
        self.app = Application(
            layout=Layout(container, focused_element=self.input_field),
            key_bindings=self.key_bindings,
            full_screen=True,  # or False?
        )

    def _handle_input(self, buff: Buffer) -> bool:
        """
        Accept handler for the input buffer.
        Takes the text from the input buffer, appends it to the output_field,
        and then clears the input buffer.
        """
        asyncio.create_task(self.client.handle_command(buff.text))
        buff.reset()
        return True

    def log_output(self, text: str):
        """Write text to the output field."""
        self.output_field.buffer.insert_text(text)
        # output_field.buffer.cursor_position = len(output_field.buffer.text)

    async def run(self):
        """Run the TUI application."""
        print("Starting Stock Alerter TUI...")
        self.client = StockAlerterClient(self.server_address, self.log_output)
        connection_task = asyncio.create_task(self.client.connect())
        try:
            self.log_output("Press Ctrl+C or Ctrl+Q to exit.\n")
            await self.app.run_async()
        except Exception as e:
            self.log_output(f"TUI Error: {e}\n")
        finally:
            print("Exiting TUI... (waiting for client to close)")
            connection_task.cancel()  # if still connecting
            await self.client.close()
            print("Exited successfully.")


async def main_tui():
    """Main function to run the TUI."""
    tui = StockAlerterTUI(DEFAULT_SERVER_ADDRESS)
    await tui.run()


if __name__ == "__main__":
    asyncio.run(main_tui())
