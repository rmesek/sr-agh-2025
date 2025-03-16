import socket
import threading

# Type definitions
type Socket = socket.socket
type RetAddress = socket._RetAddress

BUFF_SIZE = 1024
UDP_BUFF_SIZE = 1024
MESSAGE_DELIMITER = b"\0"


def _check_mtu_warning(bytes_send: int) -> bool:
    """Check if the message size exceeds the MTU warning threshold."""
    mtu_limit = 1500
    if bytes_send > mtu_limit:
        print(f"Warning: Message exceeds MTU limit ({bytes_send} > {mtu_limit})!")
        return True
    return False


def _check_buffer_size_warning(bytes_send: int) -> bool:
    """Check if the message size exceeds the buffer size warning threshold."""
    buffer_limit = UDP_BUFF_SIZE
    if bytes_send > buffer_limit:
        print(f"Warning: Message exceeds buffer limit ({bytes_send} > {buffer_limit})!")
        return True
    return False


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
    """Thread function to listen for TCP messages."""
    while True:
        try:
            message = receive_message(tcp_socket)
            print(message)
        except Exception as e:
            print(f"Error receiving message: {e}")
            break
    tcp_socket.close()
    print("Connection to server closed.")


def udp_listener(udp_socket: Socket):
    """Thread function to listen for UDP messages."""
    while True:
        try:
            buff, address = udp_socket.recvfrom(UDP_BUFF_SIZE)
            print(f"[UDP{address}]{buff.decode()}")
        except Exception as e:
            print(f"Error receiving UDP message: {e}")
            break
    udp_socket.close()
    print("UDP listener closed.")


def main():
    prompt_string = "Enter server address (e.g. 127.0.0.1:12345): "
    host, port = input(prompt_string).strip().split(":")
    port = int(port)

    # Create a TCP socket
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.connect((host, port))
    client_host, client_port = tcp_socket.getsockname()
    print(f"Connected to server at {host}:{port} as {client_host}:{client_port}")

    # Receive the nickname prompt and send the nickname.
    prompt = receive_message(tcp_socket)
    nickname = input(prompt)
    send_message(tcp_socket, nickname)

    # Start a thread to receive TCP messages
    tcp_listener_thread = threading.Thread(target=tcp_listener, args=(tcp_socket,))
    tcp_listener_thread.start()

    # Create a UDP socket
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Use the same port as the TCP socket for UDP
    udp_socket.bind((client_host, client_port))

    # Start a thread to listen for UDP messages
    udp_listener_thread = threading.Thread(target=udp_listener, args=(udp_socket,))
    udp_listener_thread.start()

    # Send messages to the server
    while True:
        message = input()
        if message.startswith("U "):
            # Send UDP message
            message = message[2:]
            bytes_send = udp_socket.sendto(message.encode(), (host, port))
            _check_mtu_warning(bytes_send)
            _check_buffer_size_warning(bytes_send)
        elif message.startswith("M "):
            # Send multicast message
            message = message[2:]
            # TODO: Implement multicast sending
        else:
            try:
                send_message(tcp_socket, message)
            except Exception as e:
                print(f"Error sending message: {e}")


if __name__ == "__main__":
    main()
