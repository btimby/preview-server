import os

from unittest import TestCase

from os.path import join as pathjoin, dirname

from aiohttp.test_utils import unittest_run_loop
from aiohttp import web
from aioresponses import aioresponses

import jwt

from tests.base import PreviewTestCase

from plugins import smartfile


class PreviewFormatTestCase(PreviewTestCase):
    @unittest_run_loop
    async def test_handler(self):
        "Request a preview as PDF and ensure PDF is returned."
        token = jwt.encode({'uid': 1}, smartfile.KEY, algorithm=smartfile.ALGO)

        with aioresponses(passthrough=['http://127.0.0.1']) as mock:
            # Mock call to SmartFile backend that plugin makes.
            mock.get(
                'http://api/api/2/path/data/sample.pdf',
                headers={
                    'X-Accel-Redirect': 'fixtures/sample.pdf'
                },
            )

            r = await self.client.request(
                'GET',
                '/api/2/path/data/sample.pdf',
                params={
                    'format': 'pdf',
                },
                cookies={
                    'sessionid': token.decode('utf8'),
                }
            )
        self.assertEqual(r.status, 200)
        self.assertEqual(r.headers['content-type'], 'application/pdf')
