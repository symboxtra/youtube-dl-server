from __future__ import unicode_literals

import json
import logging
import os
import random
import string
import subprocess
import sys
from collections import ChainMap
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from pprint import pformat, pprint
from threading import Thread

import youtube_dl
from bottle import Bottle, HTTPError, request, response, route, run, static_file, view
from database import YtdlDatabase, YtdlSqliteDatabase

# Setup a logger for SQL queries
logging.SQL = logging.DEBUG - 5
logging.addLevelName(logging.SQL, 'SQL')
def log_sql(self, msg, *args, **kwargs):
    if (self.isEnabledFor(logging.SQL)):
        self._log(logging.SQL, msg, args, **kwargs)
logging.Logger.sql = log_sql

log = logging.getLogger('youtube-dl-server-subscribed')
log.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(levelname)s: %(message)s')
handler.setFormatter(formatter)

log.addHandler(handler)

main_thread_db = YtdlSqliteDatabase()
print()
app = Bottle()


@app.get('/')
@view('index')
def bottle_index():
    return {
        'format_options': main_thread_db.get_format_options(),
        'failed': main_thread_db.get_download_failures(),
        'queue': main_thread_db.get_download_queue(),
        'history': main_thread_db.get_download_history(),
    }

@app.get('/video/<video_db_id:re:[0-9]*>')
@view('video')
def bottle_video_by_id(video_db_id):
    data = main_thread_db.get_video(video_db_id)

    if (data is None):
        raise HTTPError(404, f'Could not find video the requested video.')

    return {
        'item': data
    }

@app.get('/video/<extractor>/<video_online_id>')
@view('video')
def bottle_video_by_extractor(extractor, video_online_id):
    data = main_thread_db.get_video_by_extractor_id(extractor, video_online_id)

    if (data is None):
        raise HTTPError(404, f'Could not find video the requested video.')

    return {
        'item': data
    }

@app.get('/static/<filename:re:.*>')
def bottle_static(filename):
    return static_file(filename, root='./static')

@app.get('/api/queue')
def bottle_get_queue():
    download_queue = main_thread_db.result_to_simple_type(main_thread_db.get_download_queue())
    return {
        'count': len(download_queue),
        'items': download_queue
    }

# / is for backwards compatibility with the original project
@app.post('/')
@app.post('/api/queue')
def bottle_add_to_queue():
    url = request.forms.get('url')
    request_options = {
        'url': url,
        'format': request.forms.get('format')
    }

    if (not url):
        raise HTTPError(400, "Missing 'url' query parameter")

    download(url, request_options)
    # download_executor.submit(download, url, request_options)

    return bottle_get_queue()

@app.get('/api/failed')
def bottle_get_failed():
    failed = main_thread_db.result_to_simple_type(main_thread_db.get_download_failures())
    return {
        'count': len(failed),
        'items': failed
    }

# /update is for backwards compatibility with the original project
@app.get('/update')
@app.get('/api/pip/update')
def bottle_update():
    command = ['pip', 'install', '--upgrade', 'youtube-dl']
    proc = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    output, error = proc.communicate()
    return {
        'output': output.decode('UTF-8'),
        'error':  error.decode('UTF-8')
    }


def get_ydl_options(db, request_options):
    ydl_vars = ChainMap(os.environ, db.get_settings())

    # List of all options can be found here:
    # https://github.com/ytdl-org/youtube-dl/blob/master/youtube_dl/options.py
    return {
        'format': db.get_format(request_options['format']),
        'outtmpl': ydl_vars['YDL_OUTPUT_TEMPLATE'],
        # 'download_archive': ydl_vars['YDL_ARCHIVE_FILE'],
        'writesubtitles': True,     # --write-sub
        'allsubtitles': True,       # --all-subs
        'ignoreerrors': True,       # --ignore-errors
        'continue_dl': False,       # --no-continue
        'nooverwrites': True,       # --no-overwrites
        'addmetadata': True,        # --add-metadata
        'writedescription': True,   # --write-description
        'writeinfojson': True,      # --write-info-json
        'writeannotations': True,   # --write-annotations
        'writethumbnail': True,     # --write-thumbnail
        'embedthumbnail': True,     # --embed-thumbnail
        'subtitlesformat': 'srt',   # --sub-format 'srt'
        'embedsubtitles': True,     # --embed-subs
        'merge_output_format': 'mkv',  # --merge-output-format 'mkv'
        'recodevideo': 'mkv',       # --recode-video 'mkv'
        # 'logger': log
    }

def download(url, request_options):

    log.info(f'Processing request for {url}...')

    # Open a connection to the database
    child_thread_db = YtdlSqliteDatabase()
    ydl_options = get_ydl_options(child_thread_db, request_options)

    with youtube_dl.YoutubeDL(ydl_options) as ydl:

        # Download and extract the video metadata
        data = ydl.extract_info(url, download=False)
        log.debug(pformat(data))

        if ('_type' in data):

            if (data['_type'] == 'playlist'):
                download_playlist(child_thread_db, data, request_options)
            else:
                download_channel(child_thread_db, data, request_options)

        else:
            download_video(child_thread_db, data, request_options)

def download_channel(db, ytdl_info, request_options):
    '''
    Download all videos from the specified channel.
    '''

    ytdl_info = normalize_fields(ytdl_info)

    db.insert_extractor(ytdl_info)
    channel_db_id = db.insert_collection(ytdl_info, YtdlDatabase.collection.CHANNEL)

    total_vids = len(ytdl_info['entries'])
    video_ids = []
    for i, video_info in enumerate(ytdl_info['entries']):

        log.info(f'Processing channel entry {i + 1} of {total_vids}: {ytdl_pretty_name(ytdl_info)}')

        video_db_id = download_video(db, video_info, request_options)
        video_ids.append(video_db_id)

        # TODO: Update xref to take a list so that we can do this all at once
        db.insert_video_collection_xref(video_db_id, channel_db_id)

    return channel_db_id

def download_playlist(db, ytdl_info, request_options):
    '''
    Download all vidoes from the specified playlist.
    '''

    ytdl_info = normalize_fields(ytdl_info)

    db.insert_extractor(ytdl_info)
    playlist_db_id = db.insert_collection(ytdl_info, YtdlDatabase.collection.PLAYLIST)

    total_vids = len(ytdl_info['entries'])
    video_ids = []
    for i, video_info in enumerate(ytdl_info['entries']):

        log.info(f'Processing playlist entry {i + 1} of {total_vids}: {ytdl_pretty_name(ytdl_info)}')

        video_db_id = download_video(db, video_info, request_options)
        video_ids.append(video_db_id)

        # TODO: Update xref to take a list so that we can do this all at once
        db.insert_video_collection_xref(video_db_id, playlist_db_id, ordered_index=i + 1)

    return playlist_db_id

def download_video(db, ytdl_info, request_options):
    '''
    Download the specified video.
    '''

    ytdl_info = normalize_fields(ytdl_info)

    # Check if the video already exists
    video_data = db.get_video_by_extractor_id(ytdl_info['extractor'], ytdl_info['id'])

    needs_download = True
    if (video_data):
        # TODO: Actively check disk to see if the path still exists
        needs_download = (not video_data['filepath_exists'])
        video_db_id = video_data['id']

        log.info(f'Video "{ytdl_info["title"]}" already exists in the database. File missing on disk?: {needs_download}')

    else:
        # Insert the video and its required counterparts
        # Automatically create the channel collection and
        # add the video to it
        db.insert_extractor(ytdl_info)
        channel_db_id = db.insert_collection(ytdl_info, YtdlDatabase.collection.CHANNEL)
        video_db_id = db.insert_video(ytdl_info, request_options['format'])

        db.insert_video_owner_xref(video_db_id, channel_db_id)

    if (needs_download):

        db.mark_download_started(video_db_id)

        print()
        log.info(f'Starting download for {ytdl_pretty_name(ytdl_info)}...\n')

        ydl_options = get_ydl_options(db, request_options)

        # Actually download the video(s)
        with youtube_dl.YoutubeDL(ydl_options) as ydl:
            return_code = ydl.download([ytdl_info['webpage_url']])
            success = (return_code == 0)

        print()
        if (success):
            log.info(f'Download completed for {ytdl_pretty_name(ytdl_info)}.')
        else:
            log.error(f'Download failed for {ytdl_pretty_name(ytdl_info)}. Ytdl returned {return_code}')

        db.mark_download_ended(video_db_id, success=success)

    return video_db_id

def normalize_fields(ytdl_info):
    '''
    Make sure any fields that we rely on exist.
    If they don't, fake them using other values or None.
    '''

    field_mapping = {
        'extractor': None,
        'extractor_key': 'extractor',
        'uploader': None,
        'uploader_id': 'uploader',
        'uploader_url': None,
        'upload_date': None,
        'title': None,
        'id': None,
        'duration': None,
        'ext': None,
        'webpage_url': None
    }

    essential = [
        'extractor',
        'extractor_key',
        'uploader',
        'uploader_id',
        'title',
        'id'
    ]

    # Loop through once and loosely fill in what we can.
    # Does not attempt to do any chaining or anything with something
    # like A -> B -> C, unless they happen to already be in order.
    for required_key, alternate in field_mapping.items():
        if (not required_key in ytdl_info or ytdl_info[required_key] is None):
            log.warning(f'Missing metadata key: {required_key}')

            ytdl_info[required_key] = None

            if (alternate in ytdl_info):
                ytdl_info[required_key] = ytdl_info[alternate]

                log.debug(f'Set {required_key} to {ytdl_info[required_key]} using {alternate}')

    # Make sure essential fields have a value no matter what
    for key in essential:
        if (ytdl_info[key] is None):
            ytdl_info[key] = generate_id()
            log.debug(f'Set {key} to {ytdl_info[key]}')

    return ytdl_info

def ytdl_pretty_name(ytdl_info):

    return f'"{ytdl_info["title"]}" [{ytdl_info["webpage_url"]}]'

def generate_id():
    return 'ytdl_' + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + '_' + \
        ''.join(random.choices(string.ascii_lowercase + string.ascii_uppercase + string.digits, k=10))

if (__name__ == '__main__'):

    # download_executor = ThreadPoolExecutor(max_workers=4)

    log.info('Updating youtube-dl to the newest version')
    update_result = bottle_update()

    if (len(update_result['output']) > 0):
        log.info(update_result['output'])
    if (len(update_result['error']) > 0):
        log.warning(update_result['error'])

    app_vars = ChainMap(os.environ, main_thread_db.get_settings())

    app.run(host=app_vars['YDL_SERVER_HOST'],
            port=app_vars['YDL_SERVER_PORT'], catchall=True, debug=True)
