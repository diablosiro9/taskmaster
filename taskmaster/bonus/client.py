import socket
import sys

SOCKET_PATH = "/tmp/taskmaster.sock"

def main():
    if len(sys.argv) < 2:
        print("Usage: client.py <command>")
        sys.exit(1)

    command = " ".join(sys.argv[1:])

    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        client.connect(SOCKET_PATH)
    except (FileNotFoundError, ConnectionRefusedError):
        print("ERR daemon not running or socket closed")
        sys.exit(1)

    client.sendall((command + "\n").encode())
    response = client.recv(4096).decode()
    print(response.strip())

    client.close()

if __name__ == "__main__":
    main()
