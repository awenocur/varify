from django.test.utils import override_settings
from django.test import TransactionTestCase
from django.core.cache import cache
from django_rq import get_worker, get_queue, get_connection
from rq.queue import get_failed_queue
import os
from varify.export._vcf import VcfExporter
import hashlib
from django import http
from StringIO import StringIO

TESTS_DIR = os.path.join(os.path.dirname(__file__), '../..')
SAMPLE_DIRS = [os.path.join(TESTS_DIR, 'samples')]

class QueueTestCase(TransactionTestCase):
    def setUp(self):
        cache.clear()
        get_queue('variants').empty()
        get_queue('default').empty()
        get_failed_queue(get_connection()).empty()

@override_settings(VARIFY_SAMPLE_DIRS=SAMPLE_DIRS)
class SampleLoadTestCase(QueueTestCase):
    def test_pipeline(self):

        # Immediately validates and creates a sample
        management.call_command('samples', 'queue')
        from django.core import management

        # Synchronously work on queue
        worker1 = get_worker('variants')
        worker2 = get_worker('default')

        # Work on variants...
        worker1.work(burst=True)
        worker2.work(burst=True)

        json = '{"ranges": [{"start": 140000000, "end": 143500000, "chrom": "'\
               '""1"}], "samples": ["NA12891", "NA12892", "NA12893"]}'
        request = http.Request()
        request._stream = StringIO(json)
        exporter = VcfExporter()
        buff = exporter.write(None, request = request)
        hash = hashlib.md5(buff.content)
        self.assertequal(hash.hexdigest(), '7d21e4d8875b0d3e9f84a0d72626c700')