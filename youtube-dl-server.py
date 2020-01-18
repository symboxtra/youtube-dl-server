from __future__ import unicode_literals

import json
import logging
import os
import subprocess
import sys
from collections import ChainMap
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from pprint import pformat, pprint
from threading import Thread

import youtube_dl
from bottle import Bottle, request, response, route, run, static_file, view
from database import YtdlSqliteDatabase

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


@app.route('/')
@view('index')
def bottle_index():
    return {
        'format_options': main_thread_db.get_format_options(),
        'failed': main_thread_db.get_download_failures(),
        'queue': main_thread_db.get_download_queue(),
        'history': main_thread_db.get_download_history(),
    }

@app.route('/static/<filename:re:.*>')
def bottle_static(filename):
    return static_file(filename, root='./static')

@app.route('/api/queue', method='GET')
def bottle_get_queue():
    download_queue = main_thread_db.result_to_simple_type(main_thread_db.get_download_queue())
    return {
        'count': len(download_queue),
        'items': download_queue
    }

# / is for backwards compatibility with the original project
@app.route('/', method='POST')
@app.route('/api/queue', method='POST')
def bottle_add_to_queue():
    url = request.forms.get('url')
    request_options = {
        'format': request.forms.get('format')
    }

    if (not url):
        log.warning('Request missing URL')
        response.status = 400
        return {'error': "Missing 'url' query parameter"}

    download_executor.submit(download, url, request_options)

    return bottle_get_queue()

@app.route('/api/failed', method='GET')
def bottle_get_failed():
    failed = main_thread_db.result_to_simple_type(main_thread_db.get_download_failures())
    return {
        'count': len(failed),
        'items': failed
    }

# /update is for backwards compatibility with the original project
@app.route('/update', method='GET')
@app.route('/api/pip/update', method='GET')
def bottle_update():
    command = ['pip', 'install', '--upgrade', 'youtube-dl']
    proc = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    output, error = proc.communicate()
    return {
        'output': output.decode('UTF-8'),
        'error':  error.decode('UTF-8')
    }


def get_ydl_options(db_settings, request_options):
    ydl_vars = ChainMap(os.environ, db_settings)

    # List of all options can be found here:
    # https://github.com/ytdl-org/youtube-dl/blob/master/youtube_dl/options.py
    return {
        'format': request_options['format'],
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
    ydl_options = get_ydl_options(child_thread_db.get_settings(), request_options)

    with youtube_dl.YoutubeDL(ydl_options) as ydl:

        # Download and extract the video metadata
        data = ydl.extract_info(url, download=False)
        log.debug(pformat(data))

        if ('_type' in data):
            log.info(f'Type is "{data["_type"]}"')
            log.error ('Playlist and channel downloads are not yet implemented')
            return

        # Insert the video into the database
        child_thread_db.insert_extractor(data)
        child_thread_db.insert_collection(data)
        video_id = child_thread_db.insert_video(data)

        # Insert the video in the download queue
        child_thread_db.mark_download_started(video_id)

        print()
        video_pretty_name = f'"{data["title"]}" [{url}]'
        log.info(f'Starting download for {video_pretty_name}...\n')

        # Actually download the video(s)
        return_code = ydl.download([url])
        success = (return_code == 0)

        print()
        if (success):
            log.info(f'Download completed for {video_pretty_name}.')
        else:
            log.error(f'Download failed for {video_pretty_name}. Ytdl returned {return_code}')

        child_thread_db.mark_download_ended(video_id, success=success)

if (__name__ == '__main__'):

    download_executor = ThreadPoolExecutor(max_workers=4)

    log.info('Updating youtube-dl to the newest version')
    update_result = bottle_update()

    if (len(update_result['output']) > 0):
        log.info(update_result['output'])
    if (len(update_result['error']) > 0):
        log.warning(update_result['error'])

    app_vars = ChainMap(os.environ, main_thread_db.get_settings())

    app.run(host=app_vars['YDL_SERVER_HOST'],
            port=app_vars['YDL_SERVER_PORT'], catchall=True, debug=True)
