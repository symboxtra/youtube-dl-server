import logging
import os
import sqlite3
from abc import ABC, abstractmethod

import version

log = logging.getLogger('youtube-dl-server-subscribed')

class YtdlDatabase(ABC):
    '''
    Abstract class for database-specific implementations.

    Any queries that do not require obvious database-specific
    extensions are implemented in the base class. Queries that require
    database-specific implementation are marked as abstract and must be
    implemented by the child class.
    '''

    @abstractmethod
    def __init__(self, connection_params={}):
        pass

    @abstractmethod
    def _begin(self):
        '''
        Start a transaction.
        '''
        pass

    @abstractmethod
    def _execute(self, qstring, parameters=[]):
        '''
        Execute the query string with the given parameters.

        return: List of dictionary-like objects that can be indexed via column name.
        '''
        pass

    @abstractmethod
    def _commit(self):
        '''
        Finalize transaction.
        '''
        pass

    @abstractmethod
    def result_to_simple_type(self, result):
        '''
        Convert the list of dictionary-like objects returned by `execute`
        into simple Python types (i.e. dict and list).
        '''
        pass

    def get_settings(self):
        '''
        Fetch the stored settings.

        These represent the settings stored in the database.
        They may be overriden by environment variables elsewhere in the program.
        '''

        return self._execute('''SELECT * FROM settings''')[0]

    def get_format(self, format_id):
        '''
        Fetch the ytdl format string associated with the given id.

        Defaults to 'best' if no format is found.
        '''

        qstring = '''
            SELECT value FROM format WHERE id = ?
        '''
        result = self._execute(qstring, [format_id])

        if (len(result) == 0):
            return 'best'

        return result[0]['value']

    def get_video(self, video_db_id):
        '''
        Fetch video information for the given video.

        Returns `None` if no such video exists.
        '''

        qstring = '''
            SELECT * FROM video AS v
                LEFT JOIN extractor AS e ON v.extractor_id = e.id
                LEFT JOIN format AS f ON v.format_id = f.id
                LEFT JOIN all_download AS a ON v.id = a.video_id
            WHERE
                v.id = ?
        '''
        result = self._execute(qstring, [video_db_id])

        if (len(result) == 0):
            return None

        return result[0]

    def get_video_by_extractor(self, extractor, online_id):
        '''
        Fetch video information for the most recent video that
        matches the given extractor and extractor-specific id.

        Returns `None` if no result is found.
        '''

        qstring = '''
            SELECT id FROM video
            WHERE
                extractor_id = (SELECT id FROM extractor WHERE name = ?)
                AND online_id = ?
            ORDER BY download_datetime DESC
        '''
        result = self._execute(qstring, [extractor, online_id])

        if (len(result) == 0):
            return None

        video_db_id = result[0]['id']

        return self.get_video(video_db_id)

    def get_video_parent_collections(self, video_db_id):
        '''
        Fetch collection information for the given video.
        '''

        qstring = '''
            SELECT * FROM collection AS c
                LEFT JOIN collection_type AS t ON c.type_id = t.id
                LEFT JOIN update_sched AS u ON c.update_sched_id = u.id
            WHERE
                c.id = ?
        '''
        return self._execute(qstring, [video_db_id])

    def get_download_history(self, max_count=15):
        '''
        Fetch up to `max_count` of the latest video downloads.
        '''

        qstring = '''SELECT * FROM download_history LIMIT ?'''
        return self._execute(qstring, [max_count])

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

    def get_download_queue(self, max_count=15):
        '''
        Get information about the currently downloading
        videos in the same format as `get_download_history`.
        '''

        qstring = '''SELECT * FROM download_queue LIMIT ?'''
        return self._execute(qstring, [max_count])

    def clear_download_queue(self):
        '''
        Clear the download queue.
        '''

        qstring = '''DELETE FROM download_in_progress'''
        self._execute(qstring)
        self._commit()

    def mark_download_started(self, video_db_id):
        '''
        Add the given video to the download queue.
        '''

        self._begin()
        qstring = '''
            INSERT INTO download_in_progress (
                video_id
            ) VALUES (?)
        '''
        self._execute(qstring, [video_db_id])
        self._commit()

    def mark_download_ended(self, video_db_id, success):
        '''
        Remove the given video from the download queue
        and mark it as a success or failure.
        '''

        self._begin()
        qstring = '''
            DELETE FROM download_in_progress
            WHERE video_id = ?
        '''
        self._execute(qstring, [video_db_id])
        self._commit()

        if (not success):
            self.mark_download_failed(video_db_id)
        else:
            self.mark_download_unfailed(video_db_id)

    def mark_download_failed(self, video_db_id):
        '''
        Add the given video to the list of failed videos.
        '''

        self._begin()
        qstring = '''
            INSERT INTO download_failed (
                video_id
            ) VALUES (?)
        '''
        self._execute(qstring, [video_db_id])
        self._commit()

    def mark_download_unfailed(self, video_db_id):
        '''
        Remove a video from the list of failed videos if present.
        '''

        self._begin()
        qstring = '''
            DELETE FROM download_failed
            WHERE video_id = ?
        '''
        self._execute(qstring, [video_db_id])
        self._commit()

    def get_download_failures(self):
        '''
        Get infomration about videos that failed to
        download.
        '''

        qstring = '''
            SELECT * FROM all_download
            WHERE video_id IN
                (SELECT video_id FROM download_failed)
        '''
        return self._execute(qstring)

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

    def _begin(self):
        # Do nothing since transactions are automatic on write with sqlite3
        pass

    def _execute(self, qstring, parameters=[]):
        cursor = self.db.execute(qstring, parameters)
        return cursor.fetchall()

    def _commit(self):
        self.db.commit()

    def result_to_simple_type(self, result):
        return [dict(row) for row in result]

    def init_new_database(self):
        '''
        Setup all database tables and default values using the initialization script.
        '''

        with open('db/sqlite-init.sql', mode='r') as f:
            qstring = f.read()

        self._begin()
        self.db.executescript(qstring)
        self._commit()

        self._begin()
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
        self._commit()

        log.info('Initialized SQLite database')

    def get_format_options(self):

        qstring = '''
            SELECT f.id, category, label, value
            FROM format AS f
            LEFT JOIN format_category AS fc
                ON f.category_id = fc.id;
        '''

        cursor = self.db.execute(qstring)

        categories = {}
        for row in cursor:
            category = row['category']
            if category not in categories:
                categories[category] = []

            categories[category].append(row)

        return categories

    def insert_extractor(self, ytdl_info):

        self._begin()
        qstring = '''
            INSERT OR IGNORE INTO extractor (
                name
            ) VALUES (?);
        '''
        cursor = self.db.execute(qstring, [
            ytdl_info['extractor']
        ])

        log.debug(f'Extractor lastrowid: {cursor.lastrowid}')

        self._commit()

    def insert_collection(self, ytdl_info):

        self._begin()
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

        self._commit()

    def insert_video(self, ytdl_info, request_options):

        self._begin()
        qstring = '''
            INSERT INTO video (
                online_id,
                extractor_id,
                url,
                title,
                format_id,
                duration_s,
                upload_date,
                filepath
            )
            VALUES (?,
                (SELECT id FROM extractor WHERE name = ?),
            ?, ?, ?, ?, ?, ?)
        '''

        # Convert date to match SQLite format
        # From YYYYMMDD to YYYY-MM-DD
        upload_date = ytdl_info['upload_date']
        if (upload_date):
            upload_date = f'{upload_date[0:4]}-{upload_date[4:6]}-{upload_date[6:8]}'

        # Generate the output file path based on the output template
        filepath_fstring = self.get_settings()['YDL_OUTPUT_TEMPLATE']
        filepath = filepath_fstring % ytdl_info

        log.debug(f'Populated output template: {filepath}')

        cursor = self.db.execute(qstring, [
            ytdl_info['id'],
            ytdl_info['extractor'],
            ytdl_info['webpage_url'],
            ytdl_info['title'],
            request_options['format'],
            ytdl_info['duration'],
            upload_date,
            filepath
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

        self._commit()

        return video_id

    def __del__(self):

        self.db.close()
