import socket
import threading

def handle_client(client_socket, address):
    """Handle a client connection."""
    print(f"Connected with {address}")
    
    while True:
        try:
            # Receive data from client
            data = client_socket.recv(1024)
            if not data:
                break
            
            message = data.decode('utf-8')
            print(f"Received from {address}: {message}")
            
            # Send response back to client
            response = f"Server received: {message}"
            client_socket.send(response.encode('utf-8'))
        except Exception as e:
            print(f"Error: {e}")
            break
    
    print(f"Connection with {address} closed")
    client_socket.close()

def start_server():
    """Start the server and listen for connections."""
    host = '127.0.0.1'  # localhost
    port = 5555
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    
    print(f"Server listening on {host}:{port}")
    
    try:
        while True:
            # Accept client connection
            client_socket, address = server.accept()
            
            # Create a new thread to handle the client
            client_handler = threading.Thread(target=handle_client, args=(client_socket, address))
            client_handler.daemon = True
            client_handler.start()
    except KeyboardInterrupt:
        print("Server shutting down...")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()