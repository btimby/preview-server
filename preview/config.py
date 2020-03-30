import os
import logging


UNIT_VALUES = {
    'd': 86400,
    'h': 3600,
    'm': 60,
    's': 1,
}


def boolean(s):
    if s is None:
        return
    return s.lower() not in ('1', 'off', 'no', 'false', 'none', '')


def interval(s):
    if s is None:
        return

    s = s.lower()
    # Default unit is seconds.
    unit = 1
    if s[-1] in UNIT_VALUES.keys():
        unit, s = s[-1], s[:-1]
        try:
            unit = UNIT_VALUES[unit]

        except KeyError:
            raise Exception('Interval unit should be one of: %s' % 
                            (', '.join(UNIT_VALUES.keys())))

    try:
        seconds = int(s)

    except ValueError:
        raise Exception('Interval must be integer followed by unit, ex: 1d')

    return seconds * unit


# Configuration
CACHE_CONTROL = interval(os.environ.get('PVS_CACHE_CONTROL'))
FILE_ROOT = os.environ.get('PVS_FILES', '/mnt/files')
DEFAULT_WIDTH = os.environ.get('PVS_DEFAULT_WIDTH', 320)
DEFAULT_HEIGHT = os.environ.get('PVS_DEFAULT_HEIGHT', 240)
MAX_WIDTH = os.environ.get('PVS_MAX_WIDTH', 800)
MAX_HEIGHT = os.environ.get('PVS_MAX_HEIGHT', 600)
DEFAULT_FORMAT = os.environ.get('PVS_DEFAULT_FORMAT', 'image')
LOGLEVEL = getattr(logging, os.environ.get('PVS_LOGLEVEL', 'WARNING').upper())
HTTP_LOGLEVEL = getattr(
    logging, os.environ.get('PVS_HTTP_LOGLEVEL', 'INFO').upper())
X_ACCEL_REDIR = os.environ.get('PVS_X_ACCEL_REDIRECT')
UID = os.environ.get('PVS_UID')
GID = os.environ.get('PVS_GID')
PORT = int(os.environ.get('PVS_PORT', '3000'))
BASE_PATH = os.environ.get('PVS_STORE')
SOFFICE_ADDR = os.environ.get('PVS_SOFFICE_ADDR', '127.0.0.1')
SOFFICE_PORT = int(os.environ.get('PVS_SOFFICE_PORT', '2002'))
SOFFICE_TIMEOUT = int(os.environ.get('PVS_SOFFICE_TIMEOUT', '12'))
SOFFICE_RETRY = int(os.environ.get('PVS_SOFFICE_RETRY', '3'))
METRICS = boolean(os.environ.get('PVS_METRICS'))
PROFILE_PATH = os.environ.get('PVS_PROFILE_PATH')
MAX_FILE_SIZE = int(os.environ.get('PVS_MAX_FILE_SIZE', '0'))
MAX_PAGES = int(os.environ.get('PVS_MAX_PAGES', '0'))
MAX_STORAGE_AGE = interval(os.environ.get('PVS_STORE_MAX_AGE'))
MAX_OFFICE_WORKERS = int(os.environ.get('PVS_MAX_OFFICE_WORKERS', 0))
