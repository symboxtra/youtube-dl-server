import json
import os
from pprint import pformat, pprint

import youtube_dl
from .db import YtdlDatabase
from .log import log
from .utils import get_env_override, get_ydl_options, normalize_fields, ytdl_pretty_name

def download(url, request_options):

    log.info(f'Processing request for {url}...')

    # Open a connection to the database
    child_thread_db = YtdlDatabase.factory(get_env_override('YDL_DB_BACKEND', default='sqlite'))
    ydl_options = get_ydl_options(child_thread_db, request_options)

    with youtube_dl.YoutubeDL(ydl_options) as ydl:

        # Download and extract the video metadata
        data = ydl.extract_info(url, download=False)
        log.debug(pformat(data))

        if ('_type' in data):

            data_type = data['_type']

            # Source code includes video, playlist, compat_list, multi_video, url, and url_transparent
            # Channels are represented as "Uploads" playlist on YouTube
            if (data_type == 'video'):
                download_video(child_thread_db, data, request_options)
            elif (data_type == 'playlist' or data_type == 'multi_video' or data_type == 'compat_list'):
                download_playlist(child_thread_db, data, request_options)
            else:
                msg = f'Unhandled ytdl response type: {data_type}'
                log.error(msg)
                return msg

        else:
            download_video(child_thread_db, data, request_options)

    return ''

def download_playlist(db, ytdl_info, request_options):
    '''
    Download all vidoes from the specified playlist.
    '''

    ytdl_info = normalize_fields(ytdl_info)

    db.insert_extractor(ytdl_info)
    playlist_db_id = db.insert_collection(ytdl_info, YtdlDatabase.collection.PLAYLIST)

    total_vids = len(ytdl_info['entries'])
    video_ids = []
    video_indices = []
    for i, video_info in enumerate(ytdl_info['entries']):

        log.info(f'Processing playlist entry {i + 1} of {total_vids}: {ytdl_pretty_name(ytdl_info)}')

        video_db_id = download_video(db, video_info, request_options)

        video_ids.append(video_db_id)
        video_indices.append(ytdl_info.get('playlist_index', i + 1))

    db.insert_video_collection_xref(video_ids, playlist_db_id, ordered_index=video_indices)

    return playlist_db_id

def download_video(db, ytdl_info, request_options):
    '''
    Download the specified video.
    '''

    # Create a youtube-dl instance
    ydl_options = get_ydl_options(db, request_options)
    ydl = youtube_dl.YoutubeDL(ydl_options)

    ytdl_info = normalize_fields(ytdl_info)

    # Check if the video already exists
    video_data = db.get_video_by_extractor_id(ytdl_info['extractor_key'], ytdl_info['id'])

    needs_download = True
    if (video_data):

        video_db_id = video_data['id']
        needs_download = not os.path.exists(video_data['filepath'])

        db.mark_file_status(video_db_id, not needs_download)

        log.info(f'Video "{ytdl_info["title"]}" already exists in the database. File missing on disk?: {needs_download}')

    else:
        # Insert the video and its required counterparts
        # Automatically create the channel collection and
        # add the video to it
        db.insert_extractor(ytdl_info)
        channel_db_id = db.insert_collection(ytdl_info, YtdlDatabase.collection.CHANNEL)

        # Use our instance to create the filepath and sneak it
        # in using the dictionary
        ytdl_info['___filepath'] = ydl.prepare_filename(ytdl_info)

        video_db_id = db.insert_video(ytdl_info, request_options['format'])

        db.insert_video_owner_xref(video_db_id, channel_db_id)

    if (needs_download):

        db.mark_download_started(video_db_id)

        print()
        log.info(f'Starting download for {ytdl_pretty_name(ytdl_info)}...\n')

        # Actually download the video(s)
        ydl.process_video_result(ytdl_info, download=True)

        # Check disk for the output file so we don't have to rely on this
        return_code = ydl._download_retcode
        success = (os.path.exists(video_data['filepath']) and return_code == 0)

        print()
        if (success):
            log.info(f'Download completed for {ytdl_pretty_name(ytdl_info)}.')
        else:
            log.error(f'Download failed for {ytdl_pretty_name(ytdl_info)}. Ytdl returned {return_code}')

        db.mark_download_ended(video_db_id, success=success)
        db.mark_file_status(video_db_id, success)

    return video_db_id