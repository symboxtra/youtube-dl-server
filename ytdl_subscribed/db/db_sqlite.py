import itertools
import os
import sqlite3
from pprint import pformat

from ..log import log
from ..utils import get_env_override, get_resource_path, get_storage_path
from ..version import __version__
from .db_base import YtdlDatabase, YtdlDatabaseError

class YtdlSqliteDatabase(YtdlDatabase):

    def __init__(self):
        '''
        Open or create the SQLite database.
        '''

        super().__init__()

        # Decide where to store the database file
        # Priority (high to low): environment, config file, default
        db_path = self.db_config.get('YDL_DB_PATH', get_storage_path('data.db'))
        db_path = get_env_override('YDL_DB_PATH', default=db_path)

        log.info(f'Using SQLite database at: {db_path}')

        self.db_path = db_path
        self.is_new_db = not os.path.exists(self.db_path)
        self.db = sqlite3.connect(db_path)
        self.db.row_factory = sqlite3.Row

        if (hasattr(log, 'sql')):
            self.db.set_trace_callback(log.sql)

        # Make sure the settings and any overrides get logged initially
        if (not self.is_new_db):
            log.debug(pformat(self.get_settings(quiet=False)))

    def do_migrations(self):

        if (self.is_new_db):
            self.init_new_database()
            self.is_new_db = False

            log.debug(pformat(self.get_settings(quiet=False)))

        self._begin()
        qstring = '''
            INSERT OR REPLACE INTO download_failed (
                video_id,
                last_fail_datetime,
                error_text
            ) SELECT
                video_id,
                start_datetime,
                'Server crash or unexpected termination'
            FROM download_in_progress
        '''
        self._execute(qstring)
        qstring = '''DELETE FROM download_in_progress'''
        self._execute(qstring)
        self._commit()

        # Make sure version stays up to date
        # TODO: Migrations first
        self._begin()
        qstring = '''UPDATE setting SET version = ?'''
        self._execute(qstring, [__version__])
        self._commit()

    def _begin(self):
        # Do nothing since transactions are automatic on write with sqlite3
        pass

    def _execute(self, qstring, parameters=[]):
        cursor = self.db.execute(qstring, parameters)
        return cursor.fetchall()

    def _commit(self):
        self.db.commit()

    def result_to_simple_type(self, result):

        # Detect single-row results
        if (len(result) > 0 and type(result[0]) != sqlite3.Row):
            return dict(result)

        # Multi-row results
        else:
            return [dict(row) for row in result]

    def init_new_database(self):
        '''
        Setup all database tables and default values using the initialization script.
        '''

        with open(get_resource_path('db/sqlite-init.sql'), mode='r') as f:
            qstring = f.read()

        self._begin()
        self.db.executescript(qstring)
        self._commit()

        self._begin()
        qstring = '''
            INSERT INTO setting (
                version,
                YDL_SERVER_PROFILE,
                YDL_SERVER_HOST,
                YDL_SERVER_PORT
            ) VALUES (?, ?, ?, ?);
        '''

        profile = get_env_override('YDL_SERVER_PROFILE', default='1')
        address = get_env_override('YDL_SERVER_HOST', default='0.0.0.0')
        port = get_env_override('YDL_SERVER_PORT', default=8080)

        # Set the default settings for a new database
        self._execute(qstring, [
            __version__,
            profile,
            address,
            port,
        ])
        self._commit()

        log.info('Initialized SQLite database')

    def insert_extractor(self, ytdl_info):

        self._begin()
        qstring = '''
            INSERT OR IGNORE INTO extractor (
                name,
                alt_name
            ) VALUES (?, ?);
        '''
        self._execute(qstring, [
            ytdl_info['extractor_key'],
            ytdl_info['extractor']
        ])

        self._commit()

        extractor = self.get_extractor_by_name(ytdl_info['extractor_key'])

        if (extractor is None):
            log.error(f'Could not retrieve extractor after insertion!')
            raise YtdlDatabaseError('Extractor insertion not found')

        return extractor['id']

    def insert_collection(self, ytdl_info, collection_type):
        '''
        Insert a new collection for the given id/extractor/type if it does not exist already.

        :return collection_db_id for the inserted or already existing collection
        '''

        self._begin()
        qstring = '''
            INSERT OR IGNORE INTO collection (
                online_id,
                online_title,
                custom_title,
                url,
                type_id,
                extractor_id
            ) VALUES (?, ?, ?, ?, ?,
                (SELECT id FROM extractor WHERE name = ?)
            );
        '''

        if (collection_type == YtdlDatabase.collection.CHANNEL):
            online_id = ytdl_info['uploader_id']
            self._execute(qstring, [
                online_id,
                ytdl_info['uploader'],
                ytdl_info['uploader'],
                ytdl_info['uploader_url'],
                collection_type,
                ytdl_info['extractor_key']
            ])

        elif (collection_type == YtdlDatabase.collection.PLAYLIST):
            online_id = ytdl_info['id']
            self._execute(qstring, [
                online_id,
                ytdl_info['title'],
                ytdl_info['title'],
                ytdl_info['webpage_url'],
                collection_type,
                ytdl_info['extractor_key']
            ])

        else:
            raise YtdlDatabaseError(f'Invalid collection type: {collection_type}')

        self._commit()

        collection = self.get_collection_by_extractor_id(ytdl_info['extractor_key'], online_id)

        if (collection is None):
            log.error(f'Could not retrieve collection after insertion!')
            raise YtdlDatabaseError('Collection insertion not found')

        return collection['id']

    def insert_video(self, ytdl_info, format_db_id = YtdlDatabase.formats.DEFAULT):
        '''
        Insert a new video. The video should not exist already.

        :return video_db_id for the inserted video
        '''

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
        if (upload_date and len(upload_date) == len('YYYYMMDD')):
            upload_date = f'{upload_date[0:4]}-{upload_date[4:6]}-{upload_date[6:8]}'

        # Grab the filepath that we snuck in
        filepath = ytdl_info['___filepath']

        log.debug(f'Populated output template: {filepath}')

        self._execute(qstring, [
            ytdl_info['id'],
            ytdl_info['extractor_key'],
            ytdl_info['webpage_url'],
            ytdl_info['title'],
            format_db_id,
            ytdl_info['duration'],
            upload_date,
            filepath
        ])

        self._commit()

        self._research_insert_uploader(ytdl_info)

        video = self.get_video_by_extractor_id(ytdl_info['extractor_key'], ytdl_info['id'])

        if (video is None):
            log.error(f'Could not retrieve video after insertion!')
            raise YtdlDatabaseError('Video insertion not found')

        return video['id']

    def insert_video_collection_xref(self, video_id, collection_id, ordered_index=-1):

        self._begin()
        qstring = '''
            INSERT OR REPLACE INTO video_collection_xref (
                video_id,
                collection_id,
                ordering_index
            ) VALUES (?, ?, ?)
        '''

        if (type(video_id) == list and type(ordered_index) == list):

            if (len(video_id) != len(ordered_index)):
                raise YtdlDatabaseError('Video ID list and video index list lengths were not equal')

            self.db.executemany(qstring, zip(
                video_id,
                itertools.repeat(collection_id),
                ordered_index
            ))

        elif (type(video_id) == list):
            self.db.executemany(qstring, zip(
                video_id,
                itertools.repeat(collection_id),
                itertools.repeat(ordered_index),
            ))

        elif (type(ordered_index) == list):
            raise YtdlDatabaseError('Indices cannot be a list when video ID is scalar')

        else:
            self._execute(qstring, [
                video_id,
                collection_id,
                ordered_index
            ])

        self._commit()

    def mark_file_status(self, video_db_id, is_present):

        self._begin()
        qstring = '''
            UPDATE video SET
                filepath_exists = ?,
                filepath_last_checked = datetime('now', 'localtime')
            WHERE
                id = ?
        '''

        self._execute(qstring, [
            is_present,
            video_db_id
        ])
        self._commit()

    def __del__(self):

        if (self.db):
            self.db.close()
