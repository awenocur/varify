import hashlib
from json import dumps
from avocado.models import DataContext
from ..base import AuthenticatedBaseTestCase


class VcfExportTestCase(AuthenticatedBaseTestCase):
    fixtures = ['test_data.json', 'test_avocado_metadata.json']

    def test_pipeline(self):
        # This first test is for 3 samples, with a range on one chromosome.
        test_params = {'ranges': [{'start': 1, 'end': 144000000, 'chrom': 1}],
                       'samples': ['NA12891', 'NA12892', 'NA12878']}
        response = self.client.post('/api/data/export/vcf/',
                                    data=dumps(test_params),
                                    content_type='application/json')
        self.assertTrue(response.get('Content-Disposition').startswith(
            'attachment; filename="all'))
        hash = hashlib.md5(response.content[-800:])

        self.assertEqual(hash.hexdigest(), 'ef50b04eed793adbd517c7030bee1e06')

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

        self.assertEqual(hash.hexdigest(), '4789737e56186ba68dfce282849fa139')

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

        self.assertEqual(hash.hexdigest(), '4be7626d2adbe46593282da2fd99dc29')
