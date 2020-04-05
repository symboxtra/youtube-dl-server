from abc import ABC, abstractmethod
from datetime import datetime

from .log import log
from .utils import get_env_override, merge_env_db_settings

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
        SERVABLE = 4

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
                LEFT JOIN format AS f ON ps.default_format = f.id
        '''

        return self._execute(qstring)[0]

    def get_settings(self, quiet=True):
        '''
        Fetch the stored settings and merge them with overrides
        from the environment.
        '''

        base_settings = self._execute('''SELECT * FROM setting''')[0]

        # Make sure the env override for active profile is taken into account
        active_profile = get_env_override('YDL_SERVER_PROFILE', default=base_settings['YDL_SERVER_PROFILE'])

        qstring = '''
            SELECT * FROM setting AS s
                LEFT JOIN profile_setting AS ps ON ps.id = ?
                LEFT JOIN format AS f ON ps.default_format = f.id
        '''
        joined_settings = self._execute(qstring, [active_profile])[0]

        return merge_env_db_settings(joined_settings, quiet=quiet)

    def get_ydl_options(self):
        '''
        Fetch the available youtube-dl option information.
        '''

        qstring = '''SELECT * FROM ydl_option'''
        return self._execute(qstring)

    def get_ydl_option(self, env_name):
        '''
        Fetch youtube-dl option information for a specific option.

        Returns `None` if the option is not found.
        '''

        qstring = '''
            SELECT * FROM ydl_option
            WHERE
                env_name = ?
        '''
        result = self._execute(qstring, [env_name])

        if (len(result) == 0):
            return None

        return result[0]

    def update_ydl_options(self):
        '''
        Update all youtube-dl options in the database.

        This refreshes the help text and the destination variable.
        '''

        from youtube_dl import options

        parser = options.parseOpts()[0]
        options = self.get_ydl_options()

        self._begin()

        for row in options:

            log.debug(row['env_name'])
            log.debug('    ' + row['cli_flag'])

            parser_opt = parser.get_option(row['cli_flag'])
            dest_var = parser_opt.dest
            help_text = parser_opt.help

            log.debug('    ' + dest_var)
            log.debug('    ' + help_text + '\n')

            qstring = '''
                UPDATE ydl_option SET
                    dest_name = ?,
                    help_text = ?
                WHERE
                    env_name = ?
            '''
            self._execute(qstring, [dest_var, help_text, row['env_name']])

        self._commit()

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
            SELECT * FROM video_details
            WHERE
                id = ?
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
            SELECT * FROM collection_details
            WHERE
                id = ?
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

    def get_recent_downloads(self, max_count=15):
        '''
        Fetch up to `max_count` of the latest video downloads.
        '''

        qstring = '''SELECT * FROM video_details ORDER BY download_datetime LIMIT ?'''
        return self._execute(qstring, [max_count])

    def get_format_options(self):
        '''
        Retrieve the format options as a dictionary of categories
        containing lists of constituents.
        '''

        qstring = '''
            SELECT f.id, category, label, value
            FROM format AS f
            LEFT JOIN format_category AS fc
                ON f.category_id = fc.id;
        '''

        results = self._execute(qstring)

        categories = {}
        for row in results:
            category = row['category']
            if category not in categories:
                categories[category] = []

            categories[category].append(row)

        return categories

    @abstractmethod
    def insert_extractor(self, ytdl_info):
        '''
        Insert a new extractor if it does not exist already.

        :return extractor_db_id for the inserted or already existing extractor

        ABSTRACT: needs to ignore duplicate conflicts
        '''
        pass

    @abstractmethod
    def insert_collection(self, ytdl_info, collection_type):
        '''
        Insert a new collection for the given id/extractor/type if it does not exist already.

        :return collection_db_id for the inserted or already existing collection

        ABSTRACT: needs to ignore duplicate conflicts
        '''
        pass

    @abstractmethod
    def insert_video(self, ytdl_info, format_db_id = formats.DEFAULT):
        '''
        Insert a new video. The video should not exist already.

        :return video_db_id for the inserted video

        ABSTRACT: formats datetime to database specific format
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

        ABSTRACT: needs to update on duplicate conflict
        '''
        pass

    def get_queued_downloads(self, max_count=15):
        '''
        Get information about the currently downloading
        videos in the same format as `get_recent_downloads`.
        '''

        qstring = '''
            SELECT * FROM video_details
            WHERE queued = 1
            LIMIT ?
        '''
        return self._execute(qstring, [max_count])

    def clear_download_queue(self):
        '''
        Clear the download queue.
        '''

        self._begin()
        qstring = '''DELETE FROM download_queued'''
        self._execute(qstring)
        self._commit()

    def clear_download_in_progress(self):
        '''
        Clear the downloads in progress.
        '''

        self._begin()
        qstring = '''DELETE FROM download_in_progress'''
        self._execute(qstring)
        self._commit()

    def mark_download_queued(self, video_db_id, not_before=None):
        '''
        Queue a download so that it will be
        downloaded anytime after `not_before`.
        '''

        if (not_before is None):
            not_before = datetime.now().strftime('%Y-%m-%d %H-%M-%S')

        self._begin()
        qstring = '''
            INSERT INTO download_queued (
                video_id,
                not_before
            ) VALUES (?, ?)
        '''
        self._execute(qstring, [video_db_id, not_before])
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

    @abstractmethod
    def mark_file_status(self, video_db_id, is_present):
        '''
        Mark a given video's file as present or missing
        on disk.

        ABSTRACT: needs to use date/time functions
        '''
        pass

    def mark_file_present(self, video_db_id):
        '''
        Mark a given video's file as present on disk.
        '''
        self.mark_file_status(video_db_id, True)

    def mark_file_missing(self, video_db_id):
        '''
        Mark a given video's file as missing on disk.
        '''
        self.mark_file_status(video_db_id, False)

    def get_failed_downloads(self):
        '''
        Get infomration about videos that failed to
        download.
        '''

        qstring = '''
            SELECT * FROM video_details
            WHERE failed = 1
        '''
        return self._execute(qstring)

    def _research_insert_uploader(self, ytdl_info):
        '''
        Record alternate options for `uploader` and `uploader_id`
        for later research.
        '''

        self._begin()
        qstring = '''
            INSERT INTO _uploader_alternative (
                extractor,
                webpage_url,
                uploader_id,
                uploader,
                uploader_url,
                creator,
                channel_id,
                channel,
                channel_url,
                playlist_uploader_id,
                playlist_uploader,
                artist,
                album_artist
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''

        self._execute(qstring, [
            ytdl_info.get('extractor_key'),
            ytdl_info.get('webpage_url'),
            ytdl_info.get('uploader_id'),
            ytdl_info.get('uploader'),
            ytdl_info.get('uploader_url'),
            ytdl_info.get('creator'),
            ytdl_info.get('channel_id'),
            ytdl_info.get('channel'),
            ytdl_info.get('channel_url'),
            ytdl_info.get('playlist_uploader_id'),
            ytdl_info.get('playlist_uploader'),
            ytdl_info.get('artist'),
            ytdl_info.get('album_artist')
        ])
        self._commit()
