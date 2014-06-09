import logging
import vcf
from avocado.export._base import BaseExporter
from django.conf import settings
from varify.variants.models import Variant
import os
import re
from varify.samples.models import Sample
from varify.samples.models import Result
from django.db.models import Q
import json

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
        outer_path = os.path.dirname(os.path.realpath(__file__))
        template_path = os.path.join(outer_path,
                                     '../templates/vcfexport.vcf')
        template_file = open(template_path, "r")
        template_reader = vcf.Reader(template_file)
        writer = vcf.Writer(buff, template_reader)
        template_file.close()

        if request.method == 'POST':

            data = json.load(request._stream)

            labels = data['samples'];

            allResults = Result.objects.get_query_set()
            labelCriteria = None
            for nextLabel in labels:
                nextCriterion = Q(sample__label=nextLabel)
                if labelCriteria == None:
                    labelCriteria = nextCriterion
                else:
                    labelCriteria |= nextCriterion
            selectedResults = allResults.prefetch_related(
                'sample', 'variant').prefetch_related(
                'variant__chr').filter(
                labelCriteria).order_by('variant__chr__order', 'variant__pos')
            rows = {}
            orderedRows = []
            row_call_format = vcf.model.make_calldata_tuple(['GT', 'AD', 'DP', 'GQ'])
            row_call_format._types.append('String')
            row_call_format._types.append('String')
            row_call_format._types.append('Integer')
            row_call_format._types.append('Integer')
            sampleIndexes = {}
            sampleNum = 0
            for result in selectedResults:
                sample = result.sample
                if sample.label.encode('ascii', errors='backslashreplace') not in sampleIndexes:
                    sampleIndexes[sample.label.encode('ascii', errors='backslashreplace')] = sampleNum
                    sampleNum += 1
                variant = result.variant
                if variant.id in rows:
                    next_row=rows[variant.id]
                else:
                    rsid=variant.rsid
                    if rsid:
                        rsid=rsid.encode('ascii', errors='backslashreplace')
                    next_row=vcf.model._Record(
                                 ID=rsid,
                                 CHROM=variant.chr.label,
                                 POS=variant.pos,
                                 REF=variant.ref,
                                 ALT=variant.alt,
                                 #replace the following stubs:
                                 QUAL=result.quality,
                                 FILTER=None,
                                 INFO=None, FORMAT='GT:AD:DP:GQ',
                                 sample_indexes=sampleIndexes,
                                 samples=[])
                    rows[variant.id] = next_row
                    orderedRows.append(next_row)
                next_row_call_allelicDepth = None
                if result.coverage_ref:
                    altCoverage = 0
                    if result.coverage_alt:
                        altCoverage = result.coverage_alt
                    next_row_call_allelicDepth = '{:d},{:d}'.format(result.coverage_ref, altCoverage)
                next_row_call_values = [result.genotype.value.encode('ascii', errors='backslashreplace'),
                                        next_row_call_allelicDepth,
                                        result.read_depth,
                                        result.genotype_quality]
                next_row.samples.append(vcf.model._Call(next_row, sample.label, row_call_format(*next_row_call_values)))
            for next_row in orderedRows:
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