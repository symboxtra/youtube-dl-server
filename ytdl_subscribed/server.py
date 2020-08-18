import os

from .app import app, bottle_pip_update, db
from .log import log

def main():

    if (not 'YDL_SERVER_DOCKER' in os.environ):
        log.info('Updating youtube-dl to the newest version')
        update_result = bottle_pip_update()

        if (len(update_result['output']) > 0):
            log.info(update_result['output'])
        if (len(update_result['error']) > 0):
            log.warning(update_result['error'])

    else:
        log.warning('Docker detected. youtube-dl will NOT be auto-updated')
        log.warning('Pull the newest container to stay up to date\n')

    db.update_ydl_options()

    app_vars = db.get_settings()

    app.run(host=app_vars['YDL_SERVER_HOST'],
            port=app_vars['YDL_SERVER_PORT'], catchall=True, debug=True)
