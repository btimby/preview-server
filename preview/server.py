import os
import shutil
import logging
import asyncio
import time
import functools
import threading

from os.path import join as pathjoin

from aiohttp import web
from aiohttp.web_middlewares import normalize_path_middleware

from tempfile import NamedTemporaryFile

from gs import preview_pdf
from soffice import preview_doc
from ffmpeg import preview_video
from image import preview_image


logging.basicConfig(level=logging.DEBUG)
logging.getLogger('aiohttp').setLevel(logging.INFO)


# Limits
MEGABYTE = 1024 * 1024
BUFFER_SIZE = 8 * MEGABYTE
MAX_UPLOAD = 800 * MEGABYTE

LOGGER = logging.getLogger(__name__)
VIDEO_EXTENSIONS = set([
    '3g2', '3gp', '4xm', 'a64', 'aac', 'ac3', 'act', 'adf', 'adts', 'adx',
    'aea', 'afc', 'aiff', 'alaw', 'alsa', 'amr', 'anm', 'apc', 'ape',
    'aqtitle', 'asf', 'ast', 'au', 'avi', 'avm2', 'avr', 'avs', 'bfi',
    'bink', 'bit', 'bmv', 'boa', 'brstm', 'c93', 'caf', 'cdg', 'cdxl',
    'daud', 'dfa', 'dirac', 'divx', 'dnxhd', 'dsicin', 'dts', 'dtshd',
    'dvd', 'dxa', 'ea', 'ea_cdata', 'eac3', 'epaf', 'f32be', 'f32le',
    'f4v', 'film_cpk', 'filmstrip', 'fli', 'flic', 'flc', 'flv', 'frm',
    'g722', 'g723_1', 'g729', 'gxf', 'h261', 'h263', 'h264', 'hds', 'hevc',
    'hls', 'hls', 'idf', 'iff', 'ismv', 'iss', 'iv8', 'ivf', 'jv', 'latm',
    'lavfi', 'lmlm4', 'loas', 'lvf', 'lxf', 'm4v', 'mgsts', 'microdvd',
    'mjpeg', 'mkv', 'mlp', 'mm', 'mmf', 'mov', 'mov', 'mp4', 'm4a', '3gp',
    '3g2', 'mj2', 'mp2', 'mp4', 'mpeg', 'mpegts', 'mpg', 'mpjpeg', 'mpl2',
    'mpsub', 'mtv', 'mv', 'mvi', 'mxf', 'mxg', 'nsv', 'null', 'nut', 'nuv',
    'ogg', 'ogv', 'oma', 'opus', 'oss', 'paf', 'pjs', 'pmp', 'psp',
    'psxstr', 'pva', 'pvf', 'qcp', 'r3d', 'rl2', 'rm', 'roq', 'rpl', 'rsd',
    'rso', 'rtp', 'rtsp', 's16be', 's16le', 's24be', 's24le', 's32be',
    's32le', 's8', 'sami', 'sap', 'sbg', 'sdl', 'sdp', 'sdr2', 'segment',
    'shn', 'siff', 'smjpeg', 'smk', 'smush', 'sol', 'sox', 'svcd', 'swf',
    'tak', 'tee', 'thp', 'tmv', 'truehd', 'vc1', 'vcd', 'v4l2', 'vivo',
    'vmd', 'vob', 'voc', 'vplayer', 'vqf', 'w64', 'wc3movie', 'webm',
    'webvtt', 'wmv', 'wsaud', 'wsvqa', 'wtv', 'wv', 'xa', 'xbin', 'xmv',
    'xwma', 'yop'
])
IMAGE_EXTENSIONS = set([
    'bmp', 'dcx', 'gif', 'jpg', 'jpeg', 'png', 'psd', 'tiff', 'tif', 'xbm',
    'xpm'
])
DOCUMENT_EXTENSIONS = set([
    'dot', 'docm', 'dotx', 'dotm', 'psw', 'doc', 'xls', 'ppt', 'wpd',
    'wps', 'csv', 'sdw', 'sgl', 'vor', 'docx', 'xlsx', 'pptx', 'xlsm',
    'xltx', 'xltm', 'xlt', 'xlw', 'dif', 'rtf', 'pxl', 'pps', 'ppsx',
    'odt', 'ods', 'odp'
])

# Configuration
# TODO: Take this from config.
FILE_ROOT = os.environ.get('FILE_ROOT', '/mnt/files')
WIDTH = os.environ.get('WIDTH', 320)
HEIGHT = os.environ.get('HEIGHT', 240)
MAX_WIDTH = os.environ.get('MAX_WIDTH', 800)
MAX_HEIGHT = os.environ.get('MAX_HEIGHT', 600)


def run_in_executor(f):
    @functools.wraps(f)
    def inner(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(None, functools.partial(f, *args, **kwargs))
    return inner


async def info(request):
    return web.Response(text="OK")


async def _get_params(request):
    """
    """

    @run_in_executor
    def _upload(upload):
        extension = os.path.splitext(upload.filename)[1]
        with NamedTemporaryFile(delete=False, suffix=extension) as t:
            shutil.copyfileobj(upload.file, t, BUFFER_SIZE)
        return t.name

    if request.method == 'POST':
        data = await request.post()

    else:
        data = request.query

    path, upload = data.get('path'), data.get('file')
    width = int(data.get('width', WIDTH))
    height = int(data.get('height', HEIGHT))
    width, height = min(width, MAX_WIDTH), min(height, MAX_HEIGHT)

    if request.method == 'GET':
        path = pathjoin(FILE_ROOT, path)

    if upload:
        path = await _upload(upload)

    if not os.path.isfile(path):
        raise web.HTTPNotFound()

    return data, path, width, height


@run_in_executor
def _preview(path, width, height):
    extension = os.path.splitext(path)[1]
    LOGGER.debug('file: %s, extension: %s', path, extension)

    if extension == '.pdf':
        return preview_pdf(path, width, height)

    elif extension[1:] in DOCUMENT_EXTENSIONS:
        return preview_doc(path, width, height)

    elif extension[1:] in VIDEO_EXTENSIONS:
        return preview_video(path, width, height)

    elif extension[1:] in IMAGE_EXTENSIONS:
        # Resize image and return.
        return preview_image(path, width, height)

    else:
        raise web.HTTPBadRequest()


async def preview(request):
    try:
        data, path, width, height = await _get_params(request)
        blob = await _preview(path, width, height)

        response = web.StreamResponse()
        response.content_length = len(blob)
        response.content_type = 'image/png'
        response.headers['Cache-Control'] = 'max-age=300, public'
        await response.prepare(request)
        await response.write(blob)

        return response

    except Exception as e:
        LOGGER.exception(e)
        raise web.HTTPInternalServerError()


def main():
    app = web.Application(
        client_max_size=MAX_UPLOAD, middlewares=[normalize_path_middleware()])
    app.add_routes([web.get('/', info)])
    app.add_routes([web.post('/preview/', preview), web.get('/preview/', preview)])
    web.run_app(app, port=3000)


if __name__ == '__main__':
    main()