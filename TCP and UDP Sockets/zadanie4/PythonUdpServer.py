import socket

serverPort = 9008
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
serverSocket.bind(("", serverPort))
buff = []

print("PYTHON UDP SERVER")

while True:
    buff, address = serverSocket.recvfrom(1024)
    print("python udp server received msg: " + str(buff, "utf8"))

    if buff == b"Ping Java Udp!":
        serverSocket.sendto(bytes("Pong Java Udp!", "utf8"), address)
    elif buff == b"Ping Python Udp!":
        serverSocket.sendto(bytes("Pong Python Udp!", "utf8"), address)
    else:
        serverSocket.sendto(bytes("Pong Unknown Udp!", "utf8"), address)
