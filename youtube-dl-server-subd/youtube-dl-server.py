from __future__ import unicode_literals

import json
import logging
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pprint import pformat, pprint

import youtube_dl
from bottle import Bottle, HTTPError, redirect, request, response, route, run, static_file, view
from database import YtdlDatabase, YtdlSqliteDatabase
from log import log
from utils import get_env_override_set, get_ydl_options, handle_servable_filepath, normalize_fields, ytdl_pretty_name

log.setLevel(logging.DEBUG)

main_thread_db = YtdlSqliteDatabase()
print()
app = Bottle()


@app.get('/')
@view('index')
def bottle_index():
    return {
        'format_options': main_thread_db.get_format_options(),
        'default_format': main_thread_db.get_settings()['default_format'],
        'failed': main_thread_db.get_failed_downloads(),
        'queue': main_thread_db.get_queued_downloads(),
        'history': main_thread_db.get_recent_downloads(),
    }

@app.get('/collection/<collection_db_id:re:[0-9]*>')
@view('collection')
def bottle_collection_by_id(collection_db_id):
    data = main_thread_db.get_collection(collection_db_id)

    if (data is None):
        raise HTTPError(404, 'Could not find the requested collection.')

    return {
        'item': data
    }

@app.get('/collection/<extractor>/<collection_online_id>')
@view('collection')
def bottle_collection_by_extractor(extractor, collection_online_id):
    data = main_thread_db.get_collection_by_extractor_id(extractor, collection_online_id)

    if (data is None):
        raise HTTPError(404, 'Could not find the requested collection.')

    return {
        'item': data
    }

@app.get('/video/<video_db_id:re:[0-9]*>')
@view('video')
def bottle_video_by_id(video_db_id):
    data = main_thread_db.get_video(video_db_id)

    if (data is None):
        raise HTTPError(404, 'Could not find the requested video.')

    data = handle_servable_filepath(main_thread_db, data)

    return {
        'item': data
    }

@app.get('/video/<extractor>/<video_online_id>')
@view('video')
def bottle_video_by_extractor(extractor, video_online_id):
    data = main_thread_db.get_video_by_extractor_id(extractor, video_online_id)

    if (data is None):
        raise HTTPError(404, 'Could not find the requested video.')

    data = handle_servable_filepath(main_thread_db, data)

    return {
        'item': data
    }

@app.get('/settings')
@view('settings')
def bottle_show_settings():
    settings = main_thread_db.get_settings()

    return {
        'settings': settings,
        'ydl_options': main_thread_db.get_ydl_options(),
        'overrides': get_env_override_set(settings)
    }

@app.get('/static/<filename:re:.*>')
def bottle_static(filename):
    return static_file(filename, root='./static')

@app.get('/api/queue')
def bottle_get_queue():
    download_queue = main_thread_db.result_to_simple_type(main_thread_db.get_queued_downloads())
    return {
        'count': len(download_queue),
        'items': download_queue
    }

# / is for backwards compatibility with the original project
@app.post('/')
@app.post('/api/queue')
def bottle_add_to_queue():
    url = request.forms.get('url')
    do_redirect_str = request.forms.get('redirect')

    request_options = {
        'url': url,
        'format': request.forms.get('format')
    }
    do_redirect = True
    if (not do_redirect_str is None):
        do_redirect = do_redirect_str.lower() != "false" and do_redirect_str != "0"

    if (url is None or len(url) == 0):
        raise HTTPError(400, "Missing 'url' query parameter")

    error = download(url, request_options)
    # download_executor.submit(download, url, request_options)

    if (len(error) > 0):
        raise HTTPError(500, error)

    if (do_redirect):
        return redirect('/')

    return bottle_get_queue()

@app.get('/api/failed')
def bottle_get_failed():
    failed = main_thread_db.result_to_simple_type(main_thread_db.get_failed_downloads())
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

if (__name__ == '__main__'):

    # download_executor = ThreadPoolExecutor(max_workers=4)

    if (not 'YDL_SERVER_DOCKER' in os.environ):
        log.info('Updating youtube-dl to the newest version')
        update_result = bottle_update()

        if (len(update_result['output']) > 0):
            log.info(update_result['output'])
        if (len(update_result['error']) > 0):
            log.warning(update_result['error'])

    else:
        log.warning('Docker detected. youtube-dl will not be auto-updated')
        log.warning('Pull the newest container to stay up to date\n')

    main_thread_db.update_ydl_options()

    app_vars = main_thread_db.get_settings()

    app.run(host=app_vars['YDL_SERVER_HOST'],
            port=app_vars['YDL_SERVER_PORT'], catchall=True, debug=True)
