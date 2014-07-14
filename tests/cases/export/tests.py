import os
import hashlib
from StringIO import StringIO
from json import dumps
from django import http
from django.test.utils import override_settings
from django_rq import get_worker
from varify.export._vcf import VcfExporter
from ..base import QueueTestCase

TESTS_DIR = os.path.join(os.path.dirname(__file__), '../..')
SAMPLE_DIRS = [os.path.join(TESTS_DIR, 'samples')]

@override_settings(VARIFY_SAMPLE_DIRS=SAMPLE_DIRS)
class SampleLoadTestCase(QueueTestCase):
    @staticmethod
    def prepare_request(params):
        json = dumps(params)

        # Create a nonsensical request, just so that the exporter can function.
        request = http.HttpRequest()
        request._stream = StringIO(json)
        request.META['SERVER_NAME'] = 'test'
        request.META['SERVER_PORT'] = 0
        request.method = 'POST'
        return request

    def test_pipeline(self):
        # Immediately validates and creates a sample
        from django.core import management
        management.call_command('samples', 'queue')

        # Synchronously work on queue
        worker1 = get_worker('variants')
        worker2 = get_worker('default')

        # Work on variants...
        worker1.work(burst=True)
        worker2.work(burst=True)

        exporter = VcfExporter()

        # This first test is for 3 samples, with a range on one chromosome.
        test_params = {'ranges': [{'start': 1, 'end': 144000000, 'chrom': 1}],
                       'samples': ['NA12891', 'NA12892', 'NA12878']}
        request = SampleLoadTestCase.prepare_request(test_params)
        buff = exporter.write(None, request = request)
        hash = hashlib.md5(buff.getvalue()[-500:])
        buff.close()

        self.assertEqual(hash.hexdigest(), '990fe158f2e2390a8c3bd0d673ed40d1')

        # This second test is for 2 samples, to check that the remaining one
        # is indeed being excluded.
        test_params = {'ranges': [{'start': 1, 'end': 144000000, 'chrom': 1}],
                       'samples': ['NA12891', 'NA12892']}
        request = SampleLoadTestCase.prepare_request(test_params)
        buff = exporter.write(None, request = request)
        hash = hashlib.md5(buff.getvalue()[-500:])
        buff.close()

        self.assertEqual(hash.hexdigest(), '50dd077b5c8f55366f625e44beebf203')
