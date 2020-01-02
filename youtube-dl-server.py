from __future__ import unicode_literals

import json
import logging
import os
import subprocess
import sys
from collections import ChainMap
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Thread

import youtube_dl
from bottle import Bottle, redirect, request, route, run, static_file, view
from database import YtdlSqliteDatabase

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s: %(message)s')
handler.setFormatter(formatter)

log.addHandler(handler)

db = YtdlSqliteDatabase()

# Fill global information
format_options = db.get_format_options()

app = Bottle()

app_defaults = {
    'YDL_FORMAT': '(bestvideo[vcodec^=av01][height>=1080][fps>30]/bestvideo[vcodec=vp9.2][height>=1080][fps>30]/bestvideo[vcodec=vp9][height>=1080][fps>30]/bestvideo[vcodec^=av01][height>=1080]/bestvideo[vcodec=vp9.2][height>=1080]/bestvideo[vcodec=vp9][height>=1080]/bestvideo[height>=1080]/bestvideo[vcodec^=av01][height>=720][fps>30]/bestvideo[vcodec=vp9.2][height>=720][fps>30]/bestvideo[vcodec=vp9][height>=720][fps>30]/bestvideo[vcodec^=av01][height>=720]/bestvideo[vcodec=vp9.2][height>=720]/bestvideo[vcodec=vp9][height>=720]/bestvideo[height>=720]/bestvideo)+(bestaudio[acodec=opus]/bestaudio)/best',
    'YDL_OUTPUT_TEMPLATE': '/youtube-dl/%(extractor_key)s/%(upload_date)s %(title)s [%(id)s].%(ext)s',
    'YDL_ARCHIVE_FILE': "/youtube-dl/archive.log",
    'YDL_SERVER_HOST': '0.0.0.0',
    'YDL_SERVER_PORT': 8080
}


@app.route('/')
@view('index')
def dl_queue_list():
    return {
        "format_options": format_options,
        "history": download_history,
    }


@app.route('/static/:filename#.*#')
def server_static(filename):
    return static_file(filename, root='./static')


@app.route('/', method='POST')
def addToQueue():
    url = request.forms.get("url")
    options = {
        'format': request.forms.get("format")
    }

    if not url:
        return {"success": False, "error": "/q called without a 'url' query param"}

    download_executor.submit(download, url, options)
    return redirect("/")


@app.route("/update", method="GET")
def update():
    command = ["pip", "install", "--upgrade", "youtube-dl"]
    proc = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    output, error = proc.communicate()
    return {
        "output": output.decode('ascii'),
        "error":  error.decode('ascii')
    }


def get_ydl_options(request_options):
    ydl_vars = ChainMap(os.environ, app_defaults)

    # List of all options can be found here:
    # https://github.com/ytdl-org/youtube-dl/blob/master/youtube_dl/options.py
    return {
        'format': ydl_vars['YDL_FORMAT'],
        'outtmpl': ydl_vars['YDL_OUTPUT_TEMPLATE'],
        'download_archive': ydl_vars['YDL_ARCHIVE_FILE'],
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
        'subtitlesformat': "srt",   # --sub-format "srt"
        'embedsubtitles': True,     # --embed-subs
        'merge_output_format': "mkv",  # --merge-output-format "mkv"
        'recodevideo': "mkv",       # --recode-video "mkv"
        'embedsubtitles': True,     # --embed-subs
        'logger': log
    }

def download(url, request_options):
    with youtube_dl.YoutubeDL(get_ydl_options(request_options)) as ydl:
        data = ydl.extract_info(url, download=False)
        from pprint import pprint
        pprint(data)
        download_history.append({
            "url": url,
            "title": data["title"]
        })

        # Uploader ID
        # Tags
        # Thumbnail
        # Upload date
        # Description
        # Display ID?
        # Formats -> filesize
        # Playlist ID
        # Playlist Index
        #

        # db.execute('INSERT INTO video (youtube_id, url, format, size_B) VALUES (?, ?, ?, ?)', data.)

        # ydl.download([url])


download_executor = ThreadPoolExecutor(max_workers=4)
download_history = []

print("Updating youtube-dl to the newest version")
updateResult = update()
print(updateResult["output"])
print(updateResult["error"])

print("Started download thread")

app_vars = ChainMap(os.environ, app_defaults)

app.run(host=app_vars['YDL_SERVER_HOST'],
        port=app_vars['YDL_SERVER_PORT'], debug=True)
