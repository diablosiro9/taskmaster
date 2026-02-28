import os
import socket
import threading
from socket_protocol import handle_command
from logger import log

SOCKET_PATH = "/tmp/taskmaster.sock"

class SocketServer(threading.Thread):
    def __init__(self, manager):
        super().__init__(daemon=True)
        self.manager = manager
        self.running = True

        if os.path.exists(SOCKET_PATH):
            os.remove(SOCKET_PATH)

        self.server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server.bind(SOCKET_PATH)
        self.server.listen(5)

        log("[Socket] Listening on /tmp/taskmaster.sock")

    def run(self):
        while self.running:
            try:
                conn, _ = self.server.accept()
                with conn:
                    data = conn.recv(1024)
                    if not data:
                        continue

                    command = data.decode().strip()
                    log(f"[Socket] Command received: {command}")

                    response = handle_command(self.manager, command)

                    conn.sendall((response + "\n").encode())
                    if command.strip() == "shutdown":
                        log("[Socket] Shutdown requested")
                        self.running = False
                        self.cleanup()
                        os._exit(0)

            except Exception as e:
                log(f"[Socket] Error: {e}", level="ERROR")

    def cleanup(self):
        try:
            self.server.close()
            os.remove(SOCKET_PATH)
        except Exception:
            pass
