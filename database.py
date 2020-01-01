import logging
import os
import sqlite3
from abc import ABC, abstractmethod

log = logging.getLogger(__name__)
print(__name__)

class YtdlDatabase(ABC):

    def __init__(self, connection_params = {}):

        log.error('This class should not be instantiated.')
        raise SystemError

    @abstractmethod
    def get_format_options(self):
        pass

class YtdlSqliteDatabase(YtdlDatabase):

    def __init__(self, connection_params={}):
        '''
        Open or create the sqlite database.
        '''

        if ('path' not in connection_params):
            connection_params['path'] = 'db/youtube-dl-sub.db'
            log.info(f'Using SQLite database at: {connection_params["path"]}')

        is_new_db = not os.path.exists(connection_params['path'])
        self.db = sqlite3.connect(connection_params['path'])
        self.db.row_factory = sqlite3.Row

        if (is_new_db):
            with open('db/init.sql', mode='r') as f:
                qstring = f.read()

            self.db.executescript(qstring)
            self.db.commit()

            log.info('Initialized SQLite database')

    def get_format_options(self):
        '''
        Retrieve the format options as a set of categories and their constituents.
        '''

        qstring = '''
            SELECT category, label, value
            FROM format AS f
            LEFT JOIN format_category AS fc
                ON f.category_id = fc.id;
        '''
        log.debug(qstring)
        c = self.db.execute(qstring)

        categories = {}
        for row in c:
            category = row['category']
            if category not in categories:
                categories[category] = []

            categories[category].append(row)

        return categories