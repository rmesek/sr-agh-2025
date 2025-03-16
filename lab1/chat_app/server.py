import socket
import threading

# Type definitions
type Socket = socket.socket
type RetAddress = socket._RetAddress

HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 12345  # Port to listen on (non-privileged ports are > 1023)
BUFF_SIZE = 64
MESSAGE_DELIMITER = b"\0"

clients: dict[Socket, str] = {}
clients_lock = threading.Lock()


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


def tcp_broadcast(sender_socket: Socket, message: str):
    """Broadcast a message to all connected clients except the sender."""
    with clients_lock:
        for client_socket, nickname in clients.items():
            if client_socket != sender_socket:
                try:
                    send_message(client_socket, message)
                except Exception as e:
                    print(f"Error sending message to {nickname}: {e}")


def client_thread(client_socket: Socket, address: RetAddress):
    print(f"Client connected from {address}")
    # print(f"{client_socket=}")

    try:
        # Send a prompt to the client to enter their nickname
        send_message(client_socket, "Enter your nickname: ")
        nickname = receive_message(client_socket).strip()
        with clients_lock:
            clients[client_socket] = nickname
        message = f"{nickname} has joined the chat."
        print(message)

        # Broadcast the new client's nickname to all other clients
        tcp_broadcast(client_socket, message)

        # Receive messages from the client
        while True:
            message = receive_message(client_socket)
            print(f"{nickname}: {message}")
            tcp_broadcast(client_socket, f"{nickname}: {message}")

    except Exception as e:
        print(f"Error with client {address}: {e}")

    finally:
        with clients_lock:
            if client_socket in clients:
                print(f"{clients[client_socket]} has left the chat.")
                del clients[client_socket]
        client_socket.close()
        print(f"Client {address} disconnected.")


def main():
    # Create a TCP socket
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Set socket options to allow address reuse
    tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_socket.bind((HOST, PORT))
    tcp_socket.listen()
    print(f"Server listening on {HOST}:{PORT}")

    # Accept incoming TCP connections
    while True:
        client_socket, address = tcp_socket.accept()
        thread = threading.Thread(target=client_thread, args=(client_socket, address))
        thread.start()


if __name__ == "__main__":
    main()
