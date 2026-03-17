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

                data = conn.recv(1024)
                if not data:
                    conn.close()
                    continue

                command = data.decode().strip()
                log(f"[Socket] Command received: {command}")

                # --- ATTACH ---
                if command.startswith("attach"):
                    parts = command.split()
                    if len(parts) != 2:
                        conn.sendall(b"ERR usage: attach <program>\n")
                        conn.close()
                        continue

                    prog_name = parts[1]
                    program = self.manager.programs.get(prog_name)

                    if not program:
                        conn.sendall(b"Program not found\n")
                        conn.close()
                        continue

                    for inst in program.processes:
                        if inst.state.name == "RUNNING" and getattr(inst, "is_attachable", False):
                            self.manager.pty_manager.attach(inst.pid, conn)
                            return

                    conn.sendall(b"No running attachable instance\n")
                    conn.close()
                    continue

                # --- COMMANDES NORMALES ---
                response = handle_command(self.manager, command)
                conn.sendall((response + "\n").encode())

                if command.strip() == "shutdown":
                    log("[Socket] Shutdown requested")
                    self.running = False
                    self.cleanup()
                    os._exit(0)

                conn.close()

            except Exception as e:
                log(f"[Socket] Error: {e}", level="ERROR")

    def cleanup(self):
        try:
            self.server.close()
            os.remove(SOCKET_PATH)
        except Exception:
            pass
