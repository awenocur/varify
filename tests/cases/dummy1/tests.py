import os
from django.core.cache import cache
from django.test import TestCase
from django_rq import get_queue, get_connection
from rq.queue import get_failed_queue
from django.test.utils import override_settings
from django_rq import get_worker

TESTS_DIR = os.path.join(os.path.dirname(__file__), '../..')
SAMPLE_DIRS = [os.path.join(TESTS_DIR, 'samples')]

@override_settings(VARIFY_SAMPLE_DIRS=SAMPLE_DIRS)
class dummyTestCase1(TestCase):

    def setUp(self):
        cache.clear()
        get_queue('variants').empty()
        get_queue('default').empty()
        get_failed_queue(get_connection()).empty()

    def test_dummy(self):
        worker1 = get_worker('variants')
        worker2 = get_worker('default')

        worker1.work(burst=True)
        worker2.work(burst=True)

        self.assertTrue(True, "This should be true!")