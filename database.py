import logging
import os
import sqlite3
from abc import ABC, abstractmethod

import version

log = logging.getLogger('youtube-dl-server-subscribed')

class YtdlDatabase(ABC):

    @abstractmethod
    def __init__(self, connection_params={}):
        pass

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

        if (hasattr(log, 'sql')):
            self.db.set_trace_callback(log.sql)

        if (is_new_db):
            self.init_new_database()

    def init_new_database(self):
        '''
        Setup all database tables using the initialization script.
        '''

        with open('db/init.sql', mode='r') as f:
            qstring = f.read()

        self.db.executescript(qstring)
        self.db.commit()

        qstring = '''
            INSERT INTO settings (id, version, YDL_SERVER_HOST, YDL_SERVER_PORT, YDL_OUTPUT_TEMPLATE, YDL_ARCHIVE_FILE)
            VALUES (0, ?, ?, ?, ?, ?);
        '''

        # Set the default settings for a new database
        self.db.execute(qstring, [
            version.__version__,
            '0.0.0.0',
            8080,
            '/youtube-dl/%(extractor)s/%(upload_date)s %(title)s [%(id)s].%(ext)s',
            '/youtube-dl/archive.log'
        ])
        self.db.commit()

        log.info('Initialized SQLite database')

    def get_settings(self):

        cursor = self.db.execute('SELECT * FROM settings;')

        return dict(cursor.fetchone())

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

        c = self.db.execute(qstring)

        categories = {}
        for row in c:
            category = row['category']
            if category not in categories:
                categories[category] = []

            categories[category].append(row)

        return categories
