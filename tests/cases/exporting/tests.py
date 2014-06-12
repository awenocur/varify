<<<<<<< HEAD
=======
from varify import export
>>>>>>> populated unit test for VCF exporter
from django.test.utils import override_settings
from django.test import TransactionTestCase
from django.core.cache import cache
from django_rq import get_worker, get_queue, get_connection
from rq.queue import get_failed_queue
import os
from varify.export._vcf import VcfExporter
import hashlib
<<<<<<< HEAD
from django import http
from StringIO import StringIO
=======
>>>>>>> populated unit test for VCF exporter

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

        json = '{"ranges": [{"start": 1, "end": 144000000, "chrom": "'\
               '""1"}], "samples": ["NA12891", "NA12892", "NA12878"]}'
        request = http.Request()
        request._stream = StringIO(json)
        exporter = VcfExporter()
        buff = exporter.write(None, request = request)
        hash = hashlib.md5(buff.content)
        self.assertequal(hash.hexdigest(), '97419d94bcd14a87b83185f065511f10')
