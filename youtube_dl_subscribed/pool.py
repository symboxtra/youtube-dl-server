import multiprocessing as mp
import signal

from .db import YtdlDatabase
from .log import log
from .utils import get_env_override

# Each process's unique db connection
db = None

def init_proc():
    global db
    db = YtdlDatabase.factory(get_env_override('YDL_DB_BACKEND', default='sqlite'))

class WorkPool():

    __instance = None

    @staticmethod
    def get_instance():
        if (WorkPool.__instance is None):
            WorkPool()
        return WorkPool.__instance

    def __init__(self):

        if (not WorkPool.__instance is None):
            raise Exception('WorkPool is a singleton')

        num_procs = get_env_override('YDL_MAX_PROCESSES', mp.cpu_count() // 2)

        log.debug(f'Creating process pool with {num_procs} processes')

        # Ignore the SIGINT (Ctrl-C) interrupt in the subprocesses
        preserved_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
        self.pool = mp.Pool(num_procs, initializer=init_proc)
        signal.signal(signal.SIGINT, preserved_handler)

        WorkPool.__instance = self

    def __del__(self):

        log.info('Stopping process pool...')
        self.pool.close()
        self.pool.join()
