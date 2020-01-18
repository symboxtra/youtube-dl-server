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

        with open('db/sqlite-init.sql', mode='r') as f:
            qstring = f.read()

        self.db.executescript(qstring)
        self.db.commit()

        qstring = '''
            INSERT INTO settings (
                version,
                YDL_SERVER_HOST,
                YDL_SERVER_PORT,
                YDL_OUTPUT_TEMPLATE,
                YDL_ARCHIVE_FILE
            ) VALUES (?, ?, ?, ?, ?);
        '''

        # Set the default settings for a new database
        self.db.execute(qstring, [
            version.__version__,
            '0.0.0.0',
            8080,
            './downloaded/%(extractor)s/%(uploader)s/[%(upload_date)s] %(title)s [%(id)s].%(ext)s',
            './downloaded/archive.log'
        ])
        self.db.commit()

        log.info('Initialized SQLite database')

    def get_settings(self):

        cursor = self.db.execute('SELECT * FROM settings;')

        return cursor.fetchone()

    def get_simple_history(self, max_count=15):

        qstring = '''
            SELECT * FROM download_history LIMIT ?
        '''
        cursor = self.db.execute(qstring, [max_count])

        return cursor.fetchall()

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

    def insert_extractor(self, ytdl_info):

        qstring = '''
            INSERT OR IGNORE INTO extractor (
                name
            ) VALUES (?);
        '''
        cursor = self.db.execute(qstring, [
            ytdl_info['extractor']
        ])

        log.debug(f'Extractor lastrowid: {cursor.lastrowid}')

        self.db.commit()

    def insert_collection(self, ytdl_info):

        qstring = '''
            INSERT OR IGNORE INTO collection (
                online_id,
                online_title,
                custom_title,
                url
            ) VALUES (?, ?, ?, ?);
        '''
        cursor = self.db.execute(qstring, [
            ytdl_info['uploader_id'],
            ytdl_info['uploader'],
            ytdl_info['uploader'],
            ytdl_info['uploader_url']
        ])

        log.debug(f'Collection lastrowid: {cursor.lastrowid}')

        self.db.commit()

    def insert_video(self, ytdl_info):

        self.insert_extractor(ytdl_info)
        self.insert_collection(ytdl_info)

        qstring = '''
            INSERT INTO video (
                online_id,
                extractor_id,
                url,
                title,
                format_id,
                duration_s,
                upload_date
            )
            VALUES (?,
                (SELECT id FROM extractor WHERE name = ?),
            ?, ?, ?, ?, ?)
        '''

        # Convert date to match SQLite format
        # From YYYYMMDD to YYYY-MM-DD
        upload_date = ytdl_info['upload_date']
        upload_date = f'{upload_date[0:4]}-{upload_date[4:6]}-{upload_date[6:8]}'

        cursor = self.db.execute(qstring, [
            ytdl_info['id'],
            ytdl_info['extractor'],
            ytdl_info['webpage_url'],
            ytdl_info['title'],
            1,                  # TODO: Use the actual value from the request
            ytdl_info['duration'],
            upload_date
        ])

        log.debug(f'Video lastrowid: {cursor.lastrowid}')

        qstring = '''
            INSERT INTO video_collection_xref (
                video_id,
                collection_id
            ) VALUES (
                (SELECT id FROM video AS v WHERE v.rowid = ?),
                (SELECT id FROM collection AS c WHERE c.online_id = ?)
            )
        '''

        self.db.execute(qstring, [
            cursor.lastrowid,
            ytdl_info['uploader_id']
        ])

        self.db.commit()

    def __del__(self):

        self.db.close()
