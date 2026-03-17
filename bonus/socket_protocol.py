import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from utils.enums import ProcessState

def handle_command(manager, command: str) -> str:
    parts = command.strip().split()
    if not parts:
        return "ERR empty command"

    cmd = parts[0]

    if cmd == "status":
        lines = []
        for name, prog in manager.programs.items():
            running = len([p for p in prog.processes if p.state == ProcessState.RUNNING])
            desired = prog.config.numprocs
            lines.append(f"{name} RUNNING {running}/{desired}")
        return "\n".join(lines) if lines else "OK no programs"

    elif cmd == "start":
        if len(parts) != 2:
            return "ERR usage: start <program>"
        manager.start_program(parts[1])
        return f"OK started {parts[1]}"

    elif cmd == "stop":
        if len(parts) != 2:
            return "ERR usage: stop <program>"
        manager.stop_program(parts[1])
        return f"OK stopped {parts[1]}"

    elif cmd == "reload":
        manager.reload_config()
        return "OK reload done"

    elif cmd == "shutdown":
        return "OK shutdown"

    elif cmd.startswith("attach"):
        parts = cmd.split()

        if len(parts) != 2:
            client_socket.sendall(b"Usage: attach <program[:index]>\n")
            return

        target = parts[1]

        # --- parse program:index ---
        if ":" in target:
            prog_name, idx = target.split(":", 1)
            try:
                index = int(idx)
            except ValueError:
                client_socket.sendall(b"Invalid instance index\n")
                return
        else:
            prog_name = target
            index = 0

        program = manager.programs.get(prog_name)

        if not program:
            client_socket.sendall(b"Program not found\n")
            return

        if index >= len(program.processes):
            client_socket.sendall(b"Instance index out of range\n")
            return

        inst = program.processes[index]

        if inst.state != ProcessState.RUNNING:
            client_socket.sendall(b"Instance not running\n")
            return

        if not getattr(inst, "is_attachable", False):
            client_socket.sendall(b"Instance not attachable\n")
            return

        manager.pty_manager.attach(inst.pid, client_socket)
        return

    client_socket.sendall(b"No running attachable instance\n")

    return "ERR unknown command"
