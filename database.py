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
    def get_settings(self):
        '''
        Fetch the stored settings.

        These represent the settings stored in the database.
        They may be overriden by environment variables elsewhere in the program.
        '''
        pass

    @abstractmethod
    def get_download_history(self, max_count=15):
        '''
        Fetch up to `max_count` of the latest video downloads.
        '''
        pass

    @abstractmethod
    def get_format_options(self):
        '''
        Retrieve the format options as a dictionary of categories
        containing lists of constituents.
        '''
        pass

    @abstractmethod
    def insert_extractor(self, ytdl_info):
        '''
        Insert a new extractor if it does not exist already.
        '''
        pass

    @abstractmethod
    def insert_collection(self, ytdl_info):
        '''
        Insert a new collection if it does not exist already.
        '''
        pass

    @abstractmethod
    def insert_video(self, ytdl_info):
        '''
        Insert a new video.

        This should always insert since there is no UNIQUE constraint on videos.
        '''
        pass

    @abstractmethod
    def get_download_queue(self, max_count=15):
        '''
        Get information about the currently downloading
        videos in the same format as `get_download_history`.
        '''
        pass

    @abstractmethod
    def clear_download_queue(self):
        '''
        Clear the download queue.
        '''
        pass

    @abstractmethod
    def mark_download_started(self, video_db_id):
        '''
        Add the given video to the download queue.
        '''
        pass

    @abstractmethod
    def mark_download_ended(self, video_db_id, success):
        '''
        Remove the given video from the download queue
        and mark it as a success or failure.
        '''
        pass

    @abstractmethod
    def mark_download_failed(self, video_db_id):
        '''
        Add the given video to the list of failed videos.
        '''
        pass

    @abstractmethod
    def mark_download_unfailed(self, video_db_id):
        '''
        Remove a video from the list of failed videos if present.
        '''
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

    def result_to_simple_type(self, result):
        return [dict(row) for row in result]

    def init_new_database(self):
        '''
        Setup all database tables and default values using the initialization script.
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

    def get_download_history(self, max_count=15):

        qstring = '''
            SELECT * FROM download_history LIMIT ?
        '''
        cursor = self.db.execute(qstring, [max_count])

        return cursor.fetchall()

    def get_format_options(self):

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

        # Grab the id of the video that we just inserted
        qstring = '''SELECT id FROM video AS v WHERE v.rowid = ?'''

        cursor = self.db.execute(qstring, [cursor.lastrowid])
        video_id = cursor.fetchone()['id']

        log.debug(f'Video db id: {video_id}')

        # Add it to the collection
        qstring = '''
            INSERT INTO video_collection_xref (
                video_id,
                collection_id
            ) VALUES (
                ?,
                (SELECT id FROM collection AS c WHERE c.online_id = ?)
            )
        '''

        self.db.execute(qstring, [
            video_id,
            ytdl_info['uploader_id']
        ])

        self.db.commit()

        return video_id

    def get_download_queue(self, max_count=15):

        qstring = '''
            SELECT * FROM download_queue LIMIT ?
        '''
        cursor = self.db.execute(qstring, [max_count])

        return cursor.fetchall()

    def clear_download_queue(self):

        qstring = '''DELETE FROM download_in_progress'''
        self.db.execute(qstring)
        self.db.commit()

    def mark_download_started(self, video_db_id):

        qstring = '''
            INSERT INTO download_in_progress (
                video_id
            ) VALUES (?)
        '''
        self.db.execute(qstring, [video_db_id])
        self.db.commit()

    def mark_download_ended(self, video_db_id, success):

        qstring = '''
            DELETE FROM download_in_progress
            WHERE video_id = ?
        '''
        self.db.execute(qstring, [video_db_id])

        if (not success):
            self.mark_download_failed(video_db_id)
        else:
            self.mark_download_unfailed(video_db_id)

        self.db.commit()

    def mark_download_failed(self, video_db_id):

        qstring = '''
            INSERT INTO download_failed (
                video_id
            ) VALUES (?)
        '''
        self.db.execute(qstring, [video_db_id])
        self.db.commit()

    def mark_download_unfailed(self, video_db_id):

        qstring = '''
            DELETE FROM download_failed
            WHERE video_id = ?
        '''
        self.db.execute(qstring, [video_db_id])
        self.db.commit()

    def get_download_failures(self):

        qstring = '''
            SELECT * FROM all_recent_video
            WHERE video_id IN
                (SELECT video_id FROM download_failed)
        '''
        cursor = self.db.execute(qstring)

        return cursor.fetchall()

    def __del__(self):

        self.db.close()
