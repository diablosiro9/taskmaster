import os
import pty
import tty
import termios
import select
import threading

class PTYManager:
    def __init__(self):
        self.sessions = {}
        self.attachable = set()

    def create_pty(self):
        return pty.openpty()

    def register(self, pid, master_fd):
        self.sessions[pid] = master_fd

    def attach(self, pid, client_socket):
        if pid not in self.sessions:
            client_socket.sendall(b"Process not attachable\n")
            return

        master_fd = self.sessions[pid]

        client_socket.sendall(b"Attached. Ctrl+X or type 'detach' to detach\n")

        def bridge():
            try:
                while True:
                    rlist, _, _ = select.select([client_socket, master_fd], [], [])
                    if client_socket in rlist:
                        data = client_socket.recv(1024)
                        if not data:
                            break
                        
                        # --- DETACH ---
                        if data == b"\x18":  # Ctrl+X
                            break

                        if data.strip() == b"detach":
                            break

                        os.write(master_fd, data)
                    if master_fd in rlist:
                        data = os.read(master_fd, 1024)
                        if not data:
                            break
                        client_socket.sendall(data)

            except (BrokenPipeError, ConnectionResetError):
                pass
            except Exception:
                pass
            finally:
                self.attached.discard(pid)
                try:
                    client_socket.sendall(b"\nDetached.\n")
                except:
                    pass
                    
        t = threading.Thread(target=bridge, daemon=True)
        t.start()
                    