import random
import string
from datetime import datetime
import os

from log import log

def get_env_override(var_name, default=None, quiet=True):
    '''
    Return the given variable from the environment if it exists.

    Otherwise return `default`.
    '''

    if (is_env_override(var_name)):
        if (not quiet):
            log.debug(f'{var_name} overridden by environment with value: {os.environ[var_name]}')
        return os.environ[var_name]

    else:
        return default

def is_env_override(var_name):
    '''
    Check if a settings is overriden by the environment.
    '''
    return (var_name in os.environ and len(os.environ[var_name]) > 0)

def generate_id():
    '''
    Generate an ID in the form:
    `ytdl_YYYY-MM-DD_HH-MM-SS`
    '''

    return 'ytdl_' + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") # + '_' + \
        #''.join(random.choices(string.ascii_lowercase + string.ascii_uppercase + string.digits, k=10))

def get_ydl_options(db, request_options):
    '''
    Create a dictionary of "command-line" options for use with
    ytdl's Python API.

    The options are a combination of database settings, environment overrides,
    and request values.
    '''

    ydl_vars = db.get_settings()

    # TODO: Add:
    # playliststart
    # playlistend
    # playlistitems
    # matchtitle
    # rejecttitle
    # min_views
    # max_views
    # max_filesize
    # min_filesize
    # date?
    # datebefore?
    # dateafter?
    # sleep_interval
    # subtitleslangs
    # writeautomaticsub?
    # ratelimit
    # progresshooks?

    # List of all options can be found here:
    # https://github.com/ytdl-org/youtube-dl/blob/fca6dba8b80286ae6d3ca0a60c4799c220a52650/youtube_dl/YoutubeDL.py#L141
    # https://github.com/ytdl-org/youtube-dl/blob/master/youtube_dl/options.py
    return {
        'format': db.get_format(request_options['format']),
        'outtmpl': ydl_vars['YDL_OUTPUT_TEMPLATE'],
        'writesubtitles': bool(ydl_vars['YDL_WRITE_SUB']),          # --write-sub
        'allsubtitles': bool(ydl_vars['YDL_ALL_SUBS']),             # --all-subs
        'ignoreerrors': bool(ydl_vars['YDL_IGNORE_ERRORS']),        # --ignore-errors
        'continue_dl': bool(ydl_vars['YDL_CONTINUE_DL']),           # --no-continue
        'nooverwrites': bool(ydl_vars['YDL_NO_OVERWRITES']),        # --no-overwrites
        'addmetadata': bool(ydl_vars['YDL_ADD_METADATA']),          # --add-metadata
        'writedescription': bool(ydl_vars['YDL_WRITE_DESCRIPTION']),# --write-description
        'writeinfojson': bool(ydl_vars['YDL_WRITE_INFO_JSON']),     # --write-info-json
        'writeannotations': bool(ydl_vars['YDL_WRITE_ANNOTATIONS']),# --write-annotations
        'writethumbnail': bool(ydl_vars['YDL_WRITE_THUMBNAIL']),    # --write-thumbnail
        'embedthumbnail': bool(ydl_vars['YDL_EMBED_THUMBNAIL']),    # --embed-thumbnail
        'subtitlesformat': ydl_vars['YDL_SUB_FORMAT'],              # --sub-format 'srt'
        'embedsubtitles': bool(ydl_vars['YDL_WRITE_SUB']),          # --embed-subs
        'merge_output_format': ydl_vars['YDL_MERGE_OUTPUT_FORMAT'], # --merge-output-format 'mkv'
        'recodevideo': ydl_vars['YDL_RECODE_VIDEO'],                # --recode-video 'mkv'
        'call_home': False,
        'logger': log
    }

def merge_env_db_settings(db_settings, quiet=True):
    '''
    Merge settings from the database with settings from the environment.

    Environment settings will override database settings.
    '''

    res = {}
    for key in db_settings.keys():
        res[key] = get_env_override(key, default=db_settings[key], quiet=quiet)

    return res

def normalize_fields(ytdl_info):
    '''
    Make sure any fields that we rely on exist.
    If they don't, fake them using generated values or None.

    Field information:
    https://github.com/ytdl-org/youtube-dl/blob/master/youtube_dl/extractor/common.py#L86
    '''

    field_mapping = {
        'extractor_key': None,
        'extractor': None,
        'uploader': None,
        'uploader_id': None,
        'uploader_url': None,
        'upload_date': None,
        'title': None,
        'id': None,
        'duration': None,
        'ext': None,
        'webpage_url': None
    }

    # Only id, title, and url are guarenteed by ytdl
    # https://github.com/ytdl-org/youtube-dl#mandatory-and-optional-metafields
    essential = [
        'extractor',
        'extractor_key',
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

    # Match the ytdl template's NA since we use these for the files path
    # https://github.com/ytdl-org/youtube-dl/blob/fca6dba8b80286ae6d3ca0a60c4799c220a52650/youtube_dl/YoutubeDL.py#L659
    if (ytdl_info['uploader'] is None):
        ytdl_info['uploader'] = 'NA'
    if (ytdl_info['uploader_id'] is None):
        ytdl_info['uploader_id'] = 'NA'
    # if (ytdl_info['upload_date'] is None):
    #     ytdl_info['upload_date'] = 'NA'

    return ytdl_info

def ytdl_pretty_name(ytdl_info):

    return f'"{ytdl_info["title"]}" [{ytdl_info["webpage_url"]}]'
