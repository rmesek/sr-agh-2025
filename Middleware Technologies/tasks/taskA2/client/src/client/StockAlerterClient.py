import asyncio

from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.widgets import TextArea

# output Area
output_field = TextArea(multiline=False)


def log_output(text: str):
    """
    Write text to the output field.
    """
    output_field.buffer.insert_text(text)
    # output_field.buffer.cursor_position = len(output_field.buffer.text)


# input Area
def input_accepted(buff: Buffer) -> bool | None:
    """
    Accept handler for the input buffer.
    Takes the text from the input buffer, appends it to the output_field,
    and then clears the input buffer.
    """
    input_text = buff.text
    log_output(f"Input received: {input_text}\n")
    buff.reset()


input_field = TextArea(
    height=1,
    prompt="> ",
    multiline=False,
    wrap_lines=False,
    accept_handler=input_accepted,  # call this function on Enter
)

# layout
container = HSplit([
    # top pane for output
    Window(content=BufferControl(buffer=output_field.buffer), always_hide_cursor=True),
    # separator line
    Window(height=1, char='─', style='class:line'),
    # bottom pane for input
    input_field,
])

kb = KeyBindings()  # Ctrl+C and Ctrl+Q


@kb.add('c-c', eager=True)
@kb.add('c-q', eager=True)
def _(event):
    """
    Handle Ctrl+C or Ctrl+Q to exit the application.
    """
    event.app.exit()


# create the main Application instance
application = Application(
    layout=Layout(container, focused_element=input_field),
    key_bindings=kb,
    full_screen=True  # or False?
)


async def print_hello():
    """
    An asynchronous task that runs in the background.
    It appends "Hello World" to the output field's buffer every second.
    """
    try:
        while True:
            log_output("Hello World\n")
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        # handle task cancellation gracefully when the application exits
        pass
    except Exception as e:
        # log other potential errors
        log_output("Error in print_hello: {e}\n")


async def main():
    """
    The main entry point for the asynchronous application.
    It creates the background task and runs the prompt_toolkit application.
    """
    # create a background task
    print_hello_task = asyncio.create_task(print_hello())

    # run the prompt_toolkit application asynchronously
    # this will block until the application exits (e.g., via Ctrl+C).
    await application.run_async()

    # cleanup
    print_hello_task.cancel()
    # wait for the task to finish
    try:
        await print_hello_task
    except asyncio.CancelledError:
        pass  # expected upon cancellation


if __name__ == "__main__":
    print("Starting TUI application... Press Ctrl+C or Ctrl+Q to exit.")
    asyncio.run(main())
    print("Application exited.")
