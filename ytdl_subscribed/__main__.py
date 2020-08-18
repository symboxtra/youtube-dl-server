import sys

# Execute with
# $ python ytdl_subscribed/__main__.py
# $ python -m ytdl_subscribed

if (__package__ is None and not hasattr(sys, 'frozen')):
    # direct call of __main__.py
    import os.path
    path = os.path.realpath(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(os.path.dirname(path)))

import youtube_dl_subscribed

if (__name__ == '__main__'):
    ytdl_subscribed.main()
