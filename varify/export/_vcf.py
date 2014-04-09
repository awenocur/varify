import logging
import vcf
from avocado.export._base import BaseExporter
from django.conf import settings
from varify.variants.models import Variant
import os
import re
from varify.samples.models import Sample
from django.db.models import Q

log = logging.getLogger(__name__)


class VcfExporter(BaseExporter):
    short_name = 'VCF'
    long_name = 'Variant Call Format'

    file_extension = 'vcf'
    content_type = 'text/variant-call-format'

    def write(self, iterable, buff=None, *args, **kwargs):
        header = []
        request = kwargs['request'];
        buff = self.get_file_obj(buff)
        template_path = os.path.join(settings.PROJECT_PATH,
                                     'varify/templates/vcfexport.vcf')
        template_file = open(template_path, "r")
        template_reader = vcf.Reader(template_file)
        writer = vcf.Writer(buff, template_reader)
        for record in template_reader:
            print record;
        template_file.close()

        if request.method == 'POST':
            labels = []
            for item in request._stream:
                line = re.sub('[\n\r]', '', item)
                labels.append(line)

            allSamples = Sample.objects.get_query_set()
            labelCriteria = None
            for nextLabel in labels:
                nextCriterion = Q(label=nextLabel)
                if labelCriteria == None:
                    labelCriteria = nextCriterion
            else:
                labelCriteria |= nextCriterion
            selectedSamples = allSamples.filter(labelCriteria).select_related('results').select_related('variant')
            for sample in selectedSamples:
                results = sample.results.all().select_related('variant')
                for result in results:
                    variant = result.variant
                    next_row = vcf.model._Record(ID=variant.id,
                                             CHROM=variant.chr,
                                             POS=variant.pos,
                                             REF=variant.ref,
                                             ALT=variant.alt,
                                             #replace the following stubs:
                                             QUAL=result.quality, FILTER=None,
                                             INFO=None, FORMAT='GT',
                                             sample_indexes={sample.label:0},
                                             samples=[None])
                    row_call_format = vcf.model.make_calldata_tuple(['GT'])
                    row_call_format._types.append('String')
                    next_row_call_values = [result.genotype.label.encode('ascii', errors='backslashreplace')]
                    next_row.samples = [vcf.model._Call(next_row, sample.label, row_call_format(*next_row_call_values))]
                    writer.write_record(next_row)

        else:
            for i, row_gen in enumerate(self.read(iterable,
                                                  *args, **kwargs)):
                row = []
                for data in row_gen:
                    if i == 0:
                        header.extend(data.keys())
                    row.extend(data.values())
                raw_row_params = dict(zip(header, row))
                variant_id = raw_row_params[u'id']
                selectedVariant = Variant.objects.get(pk=variant_id)
                next_row = vcf.model._Record(ID=variant_id,
                                             CHROM=selectedVariant.chr,
                                             POS=selectedVariant.pos,
                                             REF=selectedVariant.ref,
                                             ALT=selectedVariant.alt,
                                             #replace the following stubs:
                                             QUAL=0, FILTER=None,
                                             INFO=None, FORMAT=None,
                                             sample_indexes=None,
                                             samples=None)
                                             # )
                writer.write_record(next_row)

        return buff