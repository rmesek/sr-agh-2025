import socket
import threading

# Type definitions
type Socket = socket.socket
type RetAddress = socket._RetAddress

BUFF_SIZE = 64
MESSAGE_DELIMITER = b"\0"


def send_message(socket: Socket, message: str):
    """Send a message to the socket with a delimiter."""
    socket.sendall(message.encode() + MESSAGE_DELIMITER)


def receive_message(socket: Socket) -> str:
    """Receive a message from the socket until the delimiter is found."""
    chunks = []
    while True:
        chunk = socket.recv(BUFF_SIZE)
        if not chunk:
            raise ConnectionError("Socket connection broken")
        delimiter_index = chunk.find(MESSAGE_DELIMITER)
        if delimiter_index != -1:
            chunks.append(chunk[:delimiter_index])
            break
        chunks.append(chunk)
    message = b"".join(chunks).decode()
    return message


def tcp_listener(tcp_socket: Socket):
    """Thread function to listen for messages from the server."""
    while True:
        try:
            message = receive_message(tcp_socket)
            print(message)
        except Exception as e:
            print(f"Error receiving message: {e}")
            break
    tcp_socket.close()
    print("Connection to server closed.")


def main():
    prompt_string = "Enter server address (e.g. 127.0.0.1:12345): "
    host, port = input(prompt_string).strip().split(":")
    port = int(port)

    # Create a TCP socket
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.connect((host, port))

    # Receive the nickname prompt and send the nickname.
    prompt = receive_message(tcp_socket)
    nickname = input(prompt)
    send_message(tcp_socket, nickname)

    # Start a thread to receive messages from the server
    tcp_listener_thread = threading.Thread(target=tcp_listener, args=(tcp_socket,))
    tcp_listener_thread.start()

    # Send messages to the server
    while True:
        message = input()
        try:
            send_message(tcp_socket, message)
        except Exception as e:
            print(f"Error sending message: {e}")


if __name__ == "__main__":
    main()
