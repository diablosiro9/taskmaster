import yaml
from config.program_config import ProgramConfig
from process.program import Program

class ConfigLoader:
    def __init__(self, path: str):
        self.path = path

    def load(self):
        with open(self.path, "r") as f:
            data = yaml.safe_load(f)

        programs = []

        for name, cfg in data.get("programs", {}).items():
            program_cfg = ProgramConfig(
                name=name,
                cmd=cfg["cmd"],
                numprocs=cfg.get("numprocs", 1),
                autostart=cfg.get("autostart", False),
                autorestart=cfg.get("autorestart", "never"),
                exitcodes=self._parse_exitcodes(cfg.get("exitcodes")),
                startretries=cfg.get("startretries", 3),
                starttime=cfg.get("starttime", 1),
                stopsignal=self._parse_signal(cfg.get("stopsignal", "TERM")),
                stoptime=cfg.get("stoptime", 10),
                stdout=cfg.get("stdout"),
                stderr=cfg.get("stderr"),
                env=cfg.get("env"),
                workingdir=cfg.get("workingdir"),
                umask=self._parse_umask(cfg.get("umask")),
            )
            programs.append(Program(program_cfg))

        return programs

    def _parse_signal(self, sig):
        import signal
        if isinstance(sig, int):
            return sig
        return getattr(signal, f"SIG{sig}", signal.SIGTERM)

    def _parse_umask(self, umask):
        if umask is None:
            return None

        # YAML peut fournir un int (ex: 022 -> 18)
        if isinstance(umask, int):
            return umask

        # string explicite ("022")
        return int(umask, 8)

    def _parse_exitcodes(self, exitcodes):
        if exitcodes is None:
            return [0]

        # YAML: exitcodes: 0
        if isinstance(exitcodes, int):
            return [exitcodes]

        # YAML: exitcodes: [0, 2]
        if isinstance(exitcodes, list):
            return exitcodes

        # fallback défensif
        return [int(exitcodes)]
