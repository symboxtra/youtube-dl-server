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

def get_env_override_set(settings):
    '''
    Return a set of all setting names that are overriden
    by the environment.
    '''
    overriden = set()

    for key in settings.keys():
        if (is_env_override(key)):
            overriden.add(key)

    return overriden

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

    List of all options can be found at:

    https://github.com/ytdl-org/youtube-dl/blob/fca6dba8b80286ae6d3ca0a60c4799c220a52650/youtube_dl/YoutubeDL.py#L141

    https://github.com/ytdl-org/youtube-dl/blob/master/youtube_dl/options.py
    '''

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

    options = {
        'format': db.get_format(request_options['format']),
        'call_home': False,
        'logger': log
    }

    all_opts = db.get_ydl_options()
    settings = db.get_settings()

    for row in all_opts:
        env_name = row['env_name']
        dest_name = row['dest_name']

        options[dest_name] = settings[env_name]

    return options

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
