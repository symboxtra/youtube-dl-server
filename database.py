import os
import sqlite3
from abc import ABC, abstractmethod
from pprint import pformat

import version
from log import log
from utils import get_env_override, merge_env_db_settings

class YtdlDatabaseError(Exception):
    pass

class YtdlDatabase(ABC):
    '''
    Abstract class for database-specific implementations.

    Any queries that do not require obvious database-specific
    extensions are implemented in the base class. Queries that require
    database-specific implementation are marked as abstract and must be
    implemented by the child class.
    '''

    # Enums based on order of insertion for SQlite
    class profile:
        BASIC = 1
        ARCHIVAL = 2
        PLEX = 3

    class formats:
        DEFAULT = 1

    class collection:
        CHANNEL = 1
        PLAYLIST = 2

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
        Convert the list of dictionary-like objects returned by `_execute`
        into simple Python types (i.e. dict and list).
        '''
        pass

    def get_raw_settings(self):
        '''
        Fetch the settings from the database without merging
        them with overrides from the environment.
        '''

        qstring = '''
            SELECT * FROM setting AS s
                LEFT JOIN profile_setting AS ps ON ps.id = s.YDL_SERVER_PROFILE
        '''

        return self._execute(qstring)[0]

    def get_settings(self):
        '''
        Fetch the stored settings and merge them with overrides
        from the environment.
        '''

        return merge_env_db_settings(self.get_raw_settings())

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

    def get_video_by_extractor_id(self, extractor_name, online_id):
        '''
        Fetch video information for the given video.

        Returns `None` if no result is found.
        '''

        qstring = '''
            SELECT id FROM video
            WHERE
                extractor_id = (SELECT id FROM extractor WHERE name = ?)
                AND online_id = ?
            ORDER BY download_datetime DESC
        '''
        result = self._execute(qstring, [extractor_name, online_id])

        if (len(result) == 0):
            return None

        video_db_id = result[0]['id']

        return self.get_video(video_db_id)

    def get_collection(self, collection_db_id):
        '''
        Fetch collection information for the given collection.

        Returns `None` if no result is found.
        '''

        qstring = '''
            SELECT * FROM collection AS c
                LEFT JOIN collection_type AS t ON c.type_id = t.id
                LEFT JOIN update_sched AS u ON c.update_sched_id = u.id
            WHERE
                c.id = ?
        '''
        result = self._execute(qstring, [collection_db_id])

        if (len(result) == 0):
            return None

        return result[0]

    def get_collection_by_extractor_id(self, extractor_name, online_id):
        '''
        Fetch collection information for the given collection.

        Returns `None` if no result is found.
        '''

        qstring = '''
            SELECT id FROM collection
            WHERE
                extractor_id = (SELECT id FROM extractor WHERE name = ?)
                AND online_id = ?
        '''
        result = self._execute(qstring, [extractor_name, online_id])

        if (len(result) == 0):
            return None

        collection_db_id = result[0]['id']

        return self.get_collection(collection_db_id)

    def get_collections_by_video(self, video_db_id):
        '''
        Fetch collection information for the given video.
        '''

        qstring = '''
            SELECT * FROM video_collection_xref AS x
                LEFT JOIN collection AS c ON c.id = x.collection_id
                LEFT JOIN collection_type AS t ON c.type_id = t.id
                LEFT JOIN update_sched AS u ON c.update_sched_id = u.id
            WHERE
                x.video_id = ?
        '''
        return self._execute(qstring, [video_db_id])

    def get_extractor(self, extractor_db_id):
        '''
        Fetch the extractor information for the given name.

        Returns `None` if no result is found.
        '''

        qstring = '''SELECT * FROM extractor WHERE id = ?'''
        result = self._execute(qstring, [extractor_db_id])

        if (len(result) == 0):
            return None

        return result[0]

    def get_extractor_by_name(self, name):
        '''
        Fetch the extractor information for the given name.

        Returns `None` if no result is found.
        '''

        qstring = '''SELECT * FROM extractor WHERE name = ?'''
        result = self._execute(qstring, [name])

        if (len(result) == 0):
            return None

        return result[0]

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

        :return extractor_db_id for the inserted or already existing extractor
        '''
        pass

    @abstractmethod
    def insert_collection(self, ytdl_info, collection_type):
        '''
        Insert a new collection for the given id/extractor/type if it does not exist already.

        :return collection_db_id for the inserted or already existing collection
        '''
        pass

    @abstractmethod
    def insert_video(self, ytdl_info, format_db_id = formats.DEFAULT):
        '''
        Insert a new video. The video should not exist already.

        :return video_db_id for the inserted video
        '''
        pass

    def insert_video_owner_xref(self, video_id, channel_collection_id):
        '''
        Associate a video with a given channel.

        Every inserted video should be associated with a channel
        whether it was downloaded as a standalone, playlist, or channel
        download.
        '''

        self._begin()
        qstring = '''
            INSERT INTO video_owner_xref (
                video_id,
                collection_id
            ) VALUES (?, ?)
        '''

        self._execute(qstring, [
            video_id,
            channel_collection_id
        ])
        self._commit()

    @abstractmethod
    def insert_video_collection_xref(self, video_id, collection_id, ordered_index=-1):
        '''
        Associate a video with a given collection.

        If the association already exists, the ordering index will be updated.
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

        self._begin()
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
            WHERE failed = 1
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

        # Make sure the settings and any overrides get logged initially
        log.debug(pformat(merge_env_db_settings(self.get_raw_settings(), quiet=False)))

        # Make sure version stays up to date
        # TODO: Migrations first
        self._begin()
        qstring = '''UPDATE setting SET version = ?'''
        self._execute(qstring, [version.__version__])
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

        with open('db/sqlite-init.sql', mode='r') as f:
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
        self.db.execute(qstring, [
            version.__version__,
            profile,
            address,
            port,
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
                name,
                alt_name
            ) VALUES (?, ?);
        '''
        cursor = self.db.execute(qstring, [
            ytdl_info['extractor_key'],
            ytdl_info['extractor']
        ])

        log.debug(f'Extractor lastrowid: {cursor.lastrowid}')

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
            cursor = self.db.execute(qstring, [
                online_id,
                ytdl_info['uploader'],
                ytdl_info['uploader'],
                ytdl_info['uploader_url'],
                collection_type,
                ytdl_info['extractor_key']
            ])

        elif (collection_type == YtdlDatabase.collection.PLAYLIST):
            online_id = ytdl_info['id']
            cursor = self.db.execute(qstring, [
                online_id,
                ytdl_info['title'],
                ytdl_info['title'],
                ytdl_info['webpage_url'],
                collection_type,
                ytdl_info['extractor_key']
            ])

        else:
            raise YtdlDatabaseError(f'Invalid collection type: {collection_type}')

        log.debug(f'Collection lastrowid: {cursor.lastrowid}')

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
        if (upload_date):
            upload_date = f'{upload_date[0:4]}-{upload_date[4:6]}-{upload_date[6:8]}'

        # Generate the output file path based on the output template
        filepath_fstring = self.get_settings()['YDL_OUTPUT_TEMPLATE']
        filepath = filepath_fstring % ytdl_info

        log.debug(f'Populated output template: {filepath}')

        cursor = self.db.execute(qstring, [
            ytdl_info['id'],
            ytdl_info['extractor_key'],
            ytdl_info['webpage_url'],
            ytdl_info['title'],
            format_db_id,
            ytdl_info['duration'],
            upload_date,
            filepath
        ])

        log.debug(f'Video lastrowid: {cursor.lastrowid}')

        self._commit()

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

        self._execute(qstring, [
            video_id,
            collection_id,
            ordered_index
        ])
        self._commit()

    def __del__(self):

        self.db.close()
