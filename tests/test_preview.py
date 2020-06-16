import os

from unittest import TestCase

from os.path import join as pathjoin, dirname

from aiohttp.test_utils import unittest_run_loop
from aiohttp import web

from tests.base import PreviewTestCase

from preview import parse_pages
from preview.config import MAX_PAGES, boolean, interval


ROOT = dirname(dirname(__file__))
FIXTURE_SAMPLE_PDF = pathjoin(ROOT, 'fixtures/sample.pdf')
FIXTURE_SAMPLE_DOC = pathjoin(ROOT, 'fixtures/sample.doc')
FIXTURE_QUICKTIME_MOV = pathjoin(ROOT, 'fixtures/Quicktime_Video.mov')


class PreviewFormatTestCase(PreviewTestCase):
    @unittest_run_loop
    async def test_pdf(self):
        "Request a preview as PDF and ensure PDF is returned."
        r = await self.client.request(
            'GET', '/preview/', params={'format': 'pdf', 'path': FIXTURE_SAMPLE_PDF})
        self.assertEqual(r.status, 200)
        self.assertEqual(r.headers['content-type'], 'application/pdf')

    @unittest_run_loop
    async def test_image(self):
        "Request a preview as an image and ensure GIF is returned."
        r = await self.client.request(
            'GET', '/preview/', params={'format': 'image', 'path': FIXTURE_QUICKTIME_MOV})
        self.assertEqual(r.status, 200)
        self.assertEqual(r.headers['content-type'], 'image/gif')

    @unittest_run_loop
    async def test_invalid(self):
        'Request an invalid format and ensure a 400 is returned.'
        r = await self.client.request(
            'GET', '/preview/', params={'format': 'foobar', 'path': FIXTURE_SAMPLE_PDF})
        self.assertEqual(r.status, 400)


class ParsePagesTestCase(TestCase):
    def test_parse_invalid(self):
        # Ensure that empty or missing values return the default.
        self.assertEqual(parse_pages(None), (1, 1))
        self.assertEqual(parse_pages(''), (1, 1))
        # Ensure the proper exception is raised for an unparsable value.
        with self.assertRaises(web.HTTPBadRequest):
            parse_pages('1_3')
        # Ensure MAX_PAGES is enforced.
        self.assertEqual(parse_pages('1-%i' % (MAX_PAGES + 5)), (1, MAX_PAGES))

    def test_parse_valid(self):
        # Ensure a single digit can be handled.
        self.assertEqual(parse_pages('1'), (1, 1))
        # Ensure a range is parsed properly.
        self.assertEqual(parse_pages('1-5'), (1, 5))
        # Ensure special argument "all" does the right thing.
        self.assertEqual(parse_pages('all'), (1, MAX_PAGES))


class BooleanTestCase(TestCase):
    def test_parse_true(self):
        strings = [
            'true', 'True', 'TRUE', 'on', 'On', 'ON', 'yes', 'Yes', 'YES', '1',
        ]
        for s in strings:
            self.assertTrue(boolean(s) is True, '%s did not evaluate to True' % s)

    def test_parse_false(self):
        strings = [
            None, 'false', 'False', 'FALSE', 'off', 'Off', 'OFF', 'no', 'No', 'NO', '0',
        ]
        for s in strings:
            self.assertTrue(boolean(s) is False, '%s did not evaluate to False' % s)


class IntervalTestCase(TestCase):
    def test_parse_invalid(self):
        self.assertIsNone(interval(''))
        self.assertIsNone(interval(None))
        with self.assertRaises(ValueError):
            interval('1g')

    def test_parse_valid(self):
        self.assertEqual(interval('1'), 1)
        self.assertEqual(interval('1s'), 1)
        self.assertEqual(interval('5m'), 300)
        self.assertEqual(interval('500s'), 500)
        self.assertEqual(interval('007m'), 420)
