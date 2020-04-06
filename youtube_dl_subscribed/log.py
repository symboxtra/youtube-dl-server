import logging
import sys

# Setup a logger for SQL queries
logging.SQL = logging.DEBUG - 5
logging.addLevelName(logging.SQL, 'SQL')
def log_sql(self, msg, *args, **kwargs):
    if (self.isEnabledFor(logging.SQL)):
        self._log(logging.SQL, msg, args, **kwargs)
logging.Logger.sql = log_sql

def setup_logger(name):

    log = logging.getLogger(name)
    log.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(levelname)-7s: %(message)s')
    handler.setFormatter(formatter)

    log.addHandler(handler)

    return log

log = setup_logger(__package__)
log.setLevel(logging.INFO)
