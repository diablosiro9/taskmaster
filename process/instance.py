from utils.enums import ProcessState
import time

class ProcessInstance:
    def __init__(self):
        self.pid = None
        self.state = ProcessState.STOPPED
        self.exited_flag = False
        self.exit_code = None
        self.start_time = None      # timestamp du fork
        self.retry_count = 0        # nombre de tentatives de start
        self.stop_reason = None

    def mark_started(self, pid):
        self.pid = pid
        self.state = ProcessState.RUNNING
        self.exited_flag = False
        self.start_time = time.time()
        self.exit_code = None

    def mark_exited(self, exit_code=None, manual=False):
        self.state = ProcessState.STOPPED
        self.exited_flag = True
        self.exit_code = exit_code
        self.manual_stop = manual
        # on ne reset start_time ici, car il sert pour le calcul de alive_time
        # il sera réinitialisé uniquement si on relance le process
