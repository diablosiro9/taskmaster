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

    return "ERR unknown command"
