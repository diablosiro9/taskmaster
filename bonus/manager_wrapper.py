import os
import threading
import time
import pwd
import grp
import json
from process.manager import ProcessManager
from utils.enums import ProcessState
from bonus.logger import log
from bonus.webhook import send_webhook
from bonus.pty_manager import PTYManager

ALERT_FILE = os.path.join(os.path.dirname(__file__), "logs/alerts.log")
os.makedirs(os.path.dirname(ALERT_FILE), exist_ok=True)

class ManagerWrapper:
    def __init__(self, config_path, is_daemon=False):
        self.manager = ProcessManager(config_path)
        self.disabled_programs = set()
        self._child_threads = {}  # pid -> thread pour logs stdout/stderr
        self._exited_pids = set()
        self.is_daemon = is_daemon
        self.pty_manager = PTYManager()

    def log(self, message, level="INFO"):
        log(message, level, is_daemon=self.is_daemon)

    def send_alert(self, event, payload):
        if not self.is_daemon:
            return
        alert = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "event": event,
            "payload": payload,
        }
        with open(ALERT_FILE, "a+", buffering=1) as f:
            f.write(json.dumps(alert) + "\n")
        self.log(f"[ALERT] {event} {payload}", level="WARNING")
        send_webhook(alert)

    # --- start / stop / reload / tail_child comme avant ---
    def start_program(self, name):
        if name in self.disabled_programs:
            self.log(f"Program '{name}' is disabled, not starting")
            return

        program = self.manager.programs.get(name)
        if not program:
            self.log(f"Program '{name}' not found")
            return

        for inst in program.processes:
            if inst.state != ProcessState.STOPPED:
                continue

            if program.config.attachable:
                master_fd, slave_fd = self.pty_manager.create_pty()
                pid = os.fork()

                if pid == 0:
                    try:
                        os.setsid()
                        os.dup2(slave_fd, 0)
                        os.dup2(slave_fd, 1)
                        os.dup2(slave_fd, 2)
                        os.close(master_fd)
                        os.close(slave_fd)

                        if program.config.user:
                            pw = pwd.getpwnam(program.config.user)
                            os.setgid(pw.pw_gid)
                            os.setuid(pw.pw_uid)

                        os.execv("/bin/sh", ["sh", "-c", program.config.cmd])
                    except Exception as e:
                        print(f"PTY exec failed: {e}", flush=True)
                        os._exit(1)
                else:
                    os.close(slave_fd)
                    inst.mark_started(pid)
                    inst.pty_master_fd = master_fd
                    inst.is_attachable = True
                    self.pty_manager.register(pid, master_fd)
                    self.log(f"[Daemon] Started attachable '{name}' pid={pid}")
            else:
                # 👇 ancien comportement pipe
                r, w = os.pipe()
                pid = os.fork()
                if pid == 0:
                    try:
                        os.dup2(w, 1)
                        os.dup2(w, 2)
                        os.close(r)
                        os.close(w)

                        if program.config.user:
                            try:
                                pw = pwd.getpwnam(program.config.user)
                                os.setgid(pw.pw_gid)
                                os.setuid(pw.pw_uid)
                            except KeyError:
                                self.log(f"User '{program.config.user}' not found", level="ERROR")
                                os._exit(1)
                        os.execv("/bin/sh", ["sh", "-c", program.config.cmd])
                    except Exception as e:
                        print(f"Failed to exec {program.config.cmd}: {e}", flush=True)
                        os._exit(1)
                else:
                    os.close(w)
                    inst.mark_started(pid)
                    self.log(f"[Daemon] Started '{name}' with pid {pid}")
                    t = threading.Thread(target=self._tail_child, args=(pid, r, name), daemon=True)
                    t.start()

    def _tail_child(self, pid, fd, prog_name):
        seen = set()
        while True:
            try:
                data = os.read(fd, 1024)
                if not data:
                    break
                for line in data.decode(errors="ignore").splitlines():
                    if line.strip() not in seen:
                        self.log(f"[Child {pid}] {line.strip()}")
                        seen.add(line.strip())
            except OSError:
                break
        os.close(fd)
        # self.send_alert("process_exited", {"program": prog_name, "pid": pid})
        if pid not in self._exited_pids:
            self._exited_pids.add(pid)
            self.send_alert("process_exited", {"program": prog_name, "pid": pid})

    def stop_program(self, name):
        self.disabled_programs.add(name)
        program = self.manager.programs.get(name)
        if program:
            for inst in program.processes:
                if inst.state == ProcessState.RUNNING and inst.pid:
                    self.send_alert("process_stopped", {"program": name, "pid": inst.pid})
        self.manager.stop_program(name)

    def reload_config(self):
        self.manager.reload_config()
        for name, prog in self.manager.programs.items():
            if name in self.disabled_programs:
                self.log(f"[Bonus] '{name}' disabled, ignoring reload")
                continue
            desired = prog.config.numprocs
            running = len([p for p in prog.processes if p.state == ProcessState.RUNNING])
            if running < desired:
                self.log(f"[Bonus] Increasing '{name}' {running} -> {desired}")
                for _ in range(desired - running):
                    self.start_program(name)
            elif running > desired:
                self.log(f"[Bonus] Decreasing '{name}' {running} -> {desired}")
                self.manager.stop_program(name)

    def __getattr__(self, attr):
        return getattr(self.manager, attr)
