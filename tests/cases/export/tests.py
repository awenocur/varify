import hashlib
from cStringIO import StringIO
from json import dumps
from avocado.models import DataContext
from ..base import AuthenticatedBaseTestCase
from utils import TestParser


class VcfExportTestCase(AuthenticatedBaseTestCase):
    fixtures = ['test_data.json', 'test_avocado_metadata.json']

    def test_export(self):
        # This first test is for 3 samples, with a range on one chromosome.
        test_params = {'ranges': [{'start': 1, 'end': 144000000, 'chrom': 1}],
                       'samples': ['NA12891', 'VPseq004-P-A', 'NA12878']}
        response = self.client.post('/api/data/export/vcf/',
                                    data=dumps(test_params),
                                    content_type='application/json')
        self.assertTrue(response.get('Content-Disposition').startswith(
            'attachment; filename="all'))

        test_parser = TestParser(StringIO(response.content), self)
        test_parser.check_samples(('NA12891', 'VPseq004-P-A', 'NA12878'))
        test_parser.check_multi_info('EFF', 21, ['INTRON(Modifier||||LINC00875|NR_027469.1|intron.1|c.388-8026A>G|)', 'INTRON(Modifier||||FLJ39739|NR_027468.1|intron.1|c.258-8026A>G|)'])
        test_parser.check_num_records(33)
        test_parser.check_multi_field('NA12891', 22, 'AD', [0,0])

        # This second test is for 2 samples, to check that the remaining one
        # is indeed being excluded.
        test_params = {'ranges': [{'start': 1, 'end': 144000000, 'chrom': 1}],
                       'samples': ['NA12891', 'NA12892']}
        response = self.client.post('/api/data/export/vcf/',
                                    data=dumps(test_params),
                                    content_type='application/json')
        self.assertTrue(response.get('Content-Disposition').startswith(
            'attachment; filename="all'))

        test_parser = TestParser(StringIO(response.content), self)
        test_parser.check_samples(('NA12891',))
        test_parser.check_num_records(33)
        test_parser.check_multi_info('EFF', 22, ['INTRON(Modifier||||LINC00875|NR_027469.1|intron.1|c.388-8043A>G|)', 'INTRON(Modifier||||FLJ39739|NR_027468.1|intron.1|c.258-8043A>G|)'])
        test_parser.check_multi_field('NA12891', 22, 'GT', None, 'AD', [0,0])

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

        test_parser = TestParser(StringIO(response.content), self)
        test_parser.check_unordered_samples(('NA12878', 'NA12891',))
        test_parser.check_multi_info('EFF', 1959, ['INTRON(Modifier||||LOC100288142|NM_001278267.1|intron.99|c.10989-123920T>A|)', 'INTRON(Modifier||||NBPF10|NM_001039703.5|intron.68|c.8615-124812T>A|)'])
        test_parser.check_num_records(1963)