import json
import subprocess

from bottle import Bottle, HTTPError, redirect, request, response, route, run, static_file, view
from .db.db_sqlite import YtdlSqliteDatabase
from .log import log
from .utils import get_env_override_set, get_resource_path, get_storage_path, get_ydl_options, handle_servable_filepath

# TODO: Figure out how to unify opening a connection to the db
try:
    with open(get_storage_path('db_config.json')) as f:
        db_config = json.load(f)
except Exception as e:
    log.info('Could not open db_config.json. Using default connection settings.')
    log.debug(e)
    db_config = {}

db = YtdlSqliteDatabase(db_config)
app = Bottle()

@app.get('/')
@view('index')
def bottle_index():
    return {
        'format_options': db.get_format_options(),
        'default_format': db.get_settings()['default_format'],
        'failed': db.get_failed_downloads(),
        'queue': db.get_queued_downloads(),
        'history': db.get_recent_downloads(),
    }

@app.get('/collection/<collection_db_id:re:[0-9]*>')
@view('collection')
def bottle_collection_by_id(collection_db_id):
    data = db.get_collection(collection_db_id)

    if (data is None):
        raise HTTPError(404, 'Could not find the requested collection.')

    return {
        'item': data
    }

@app.get('/collection/<extractor>/<collection_online_id>')
@view('collection')
def bottle_collection_by_extractor(extractor, collection_online_id):
    data = db.get_collection_by_extractor_id(extractor, collection_online_id)

    if (data is None):
        raise HTTPError(404, 'Could not find the requested collection.')

    return {
        'item': data
    }

@app.get('/video/<video_db_id:re:[0-9]*>')
@view('video')
def bottle_video_by_id(video_db_id):
    data = db.get_video(video_db_id)

    if (data is None):
        raise HTTPError(404, 'Could not find the requested video.')

    data = handle_servable_filepath(db, data)

    return {
        'item': data
    }

@app.get('/video/<extractor>/<video_online_id>')
@view('video')
def bottle_video_by_extractor(extractor, video_online_id):
    data = db.get_video_by_extractor_id(extractor, video_online_id)

    if (data is None):
        raise HTTPError(404, 'Could not find the requested video.')

    data = handle_servable_filepath(db, data)

    return {
        'item': data
    }

@app.get('/settings')
@view('settings')
def bottle_show_settings():
    settings = db.get_settings()

    return {
        'settings': settings,
        'ydl_options': db.get_ydl_options(),
        'overrides': get_env_override_set(settings)
    }

@app.get('/static/<filename:re:.*>')
def bottle_static(filename):
    return static_file(filename, root=get_resource_path('static'))

@app.get('/api/queue')
def bottle_get_queue():
    download_queue = db.result_to_simple_type(db.get_queued_downloads())
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
    failed = db.result_to_simple_type(db.get_failed_downloads())
    return {
        'count': len(failed),
        'items': failed
    }

# /update is for backwards compatibility with the original project
@app.get('/update')
@app.get('/api/pip/update')
def bottle_pip_update():
    command = ['pip', 'install', '--upgrade', 'youtube-dl']
    proc = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    output, error = proc.communicate()
    return {
        'output': output.decode('UTF-8'),
        'error':  error.decode('UTF-8')
    }