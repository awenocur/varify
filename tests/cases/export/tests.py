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
    fixtures = ['test_avocado_metadata.json']

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
        hash = hashlib.md5(response.content[-800:])

        self.assertEqual(hash.hexdigest(), '50d3afcb560d03fa0868ed1d399b20d1')

        # This second test is for 2 samples, to check that the remaining one
        # is indeed being excluded.
        test_params = {'ranges': [{'start': 1, 'end': 144000000, 'chrom': 1}],
                       'samples': ['NA12891', 'NA12892']}
        response = self.client.post('/api/data/export/vcf/',
                                    data=dumps(test_params),
                                    content_type='application/json')
        self.assertTrue(response.get('Content-Disposition').startswith(
            'attachment; filename="all'))
        hash = hashlib.md5(response.content[-800:])

        self.assertEqual(hash.hexdigest(), 'eaa81aff34db3104fba4106adf428679')

        # This third test runs the exporter using results provided by Serrano.
        test_params = {'type': 'and',
                       'children':
                           [{'concept': 2,
                             'required': True,
                             'value':
                                 [{'value': 3,
                                   'label': 'NA12878'},
                                  {'value': 1, 'label': 'NA12891'},
                                  {'value': 2, 'label': 'NA12892'}],
                             'field': 111, 'operator': 'in'},
                            {'operator': 'in', 'field': 64,
                             'concept': 1, 'value': [1]},
                            {'concept': 1,
                             'required': False,
                             'value': [100000000, 153500000],
                             'field': 69, 'operator': 'range'}]}
        cxt = DataContext(template=True, default=True, json=dumps(test_params))
        cxt.save()
        response = self.client.get('/api/data/export/vcf/')
        self.assertTrue(response.get('Content-Disposition').startswith(
            'attachment; filename="all'))
        hash = hashlib.md5(response.content[-800:])

        self.assertEqual(hash.hexdigest(), '61ac69bba80a494aca7d57f8c5f4566f')
