import os
import hashlib
from json import dumps
from django.test.utils import override_settings
from django_rq import get_worker
from avocado.models import DataContext
from varify.export._vcf import VcfExporter
from ..base import AuthenticatedQueueTestCase

TESTS_DIR = os.path.join(os.path.dirname(__file__), '../..')
SAMPLE_DIRS = [os.path.join(TESTS_DIR, 'samples')]

@override_settings(VARIFY_SAMPLE_DIRS=SAMPLE_DIRS)
class VcfExportTestCase(AuthenticatedQueueTestCase):
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
        response = self.client.post('/api/data/export/vcf/',
                                    data=dumps(test_params),
                                    content_type='application/json')
        self.assertTrue(response.get('Content-Disposition').startswith(
            'attachment; filename="all'))
        hash = hashlib.md5(response.content[-500:])

        self.assertEqual(hash.hexdigest(), '990fe158f2e2390a8c3bd0d673ed40d1')

        # This second test is for 2 samples, to check that the remaining one
        # is indeed being excluded.
        test_params = {'ranges': [{'start': 1, 'end': 144000000, 'chrom': 1}],
                       'samples': ['NA12891', 'NA12892']}
        response = self.client.post('/api/data/export/vcf/',
                                    data=dumps(test_params),
                                    content_type='application/json')
        self.assertTrue(response.get('Content-Disposition').startswith(
            'attachment; filename="all'))
        hash = hashlib.md5(response.content[-500:])

        self.assertEqual(hash.hexdigest(), '50dd077b5c8f55366f625e44beebf203')

        # This third test runs the exporter using results provided by Serrano.
        test_params = {'type': 'and',
                       'children':
                           [{'concept': 2,
                             'language':
                                 'Sample is either NA12878, NA12891 or NA12892',
                             'required': True,
                             'value':
                                 [{'value': 15,
                                   'label': 'NA12878'},
                                  {'value': 13, 'label': 'NA12891'},
                                  {'value': 14, 'label': 'NA12892'}],
                             'field': 111, 'operator': 'in'},
                            {'operator': 'in', 'field': 64,
                             'concept': 1, 'value': [1], 'language':
                                'Chromosome is 1'},
                            {'concept': 1,
                             'language':
                                 'Position is between 100000000.0 and 153500000.0',
                             'required': False,
                             'value': [100000000, 153500000],
                             'field': 69, 'operator': 'range'}]}
        cxt = DataContext(template=True, default=True, json=dumps(test_params))
        cxt.save()