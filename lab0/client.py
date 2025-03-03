import socket
import time

def start_client():
    """Start a client that connects to the server."""
    host = '127.0.0.1'  # localhost
    port = 5555
    
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        # Connect to the server
        client.connect((host, port))
        print(f"Connected to server at {host}:{port}")
        
        # Send messages
        for i in range(5):
            message = f"Hello from client, message #{i+1}"
            client.send(message.encode('utf-8'))
            
            # Receive response
            response = client.recv(1024).decode('utf-8')
            print(f"Received: {response}")
            
            time.sleep(1)
        
        # Close the connection
        print("Closing connection")
    except ConnectionRefusedError:
        print("Failed to connect to server. Is the server running?")
    finally:
        client.close()

if __name__ == "__main__":
    start_client()