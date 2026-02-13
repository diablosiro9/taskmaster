from typing import Optional, Dict, List

class ProgramConfig:
    def __init__(
        self,
        name: str,
        cmd: str,
        numprocs: int = 1,
        autostart: bool = False,
        autorestart: str = "never",
        exitcodes: Optional[List[int]] = None,
        startretries: int = 3,
        starttime: int = 1,
        stopsignal: int = 15,
        stoptime: int = 10,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        workingdir: Optional[str] = None,
        umask: Optional[int] = None,
    ):
        self.name = name
        self.cmd = cmd
        self.numprocs = numprocs
        self.autostart = autostart
        self.autorestart = autorestart
        self.exitcodes = exitcodes or [0]
        self.startretries = startretries
        self.starttime = starttime
        self.stopsignal = stopsignal
        self.stoptime = stoptime
        self.stdout = stdout
        self.stderr = stderr
        self.env = env or {}
        self.workingdir = workingdir
        self.umask = umask
