import logging
import vcf
from django.conf import settings
import os
from varify.samples.models import Result
from django.db.models import Q
from django.core.management.base import BaseCommand
import sys

log = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "demo export of a VCF file"

    file_extension = 'vcf'
    content_type = 'text/variant-call-format'

    def handle(self, *args, **kwargs):
        buff = sys.stdout
        template_path = os.path.join(settings.PROJECT_PATH,
                                     'varify/templates/vcfexport.vcf')
        template_file = open(template_path, "r")
        template_reader = vcf.Reader(template_file)
        writer = vcf.Writer(buff, template_reader)
        template_file.close()

        labels = []
        for item in args:
            labels.append(item)

        allResults = Result.objects.get_query_set()
        labelCriteria = None
        for nextLabel in labels:
            nextCriterion = Q(sample__label=nextLabel)
            if labelCriteria == None:
                labelCriteria = nextCriterion
            else:
                labelCriteria |= nextCriterion
        selectedResults = allResults.prefetch_related('sample', 'variant').prefetch_related('variant__chr').filter(labelCriteria)
        rows = {}
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
            next_row_call_allelicDepth = None
            if result.coverage_ref:
                altCoverage = 0
                if result.coverage_alt:
                    altCoverage = result.coverage_alt
                next_row_call_allelicDepth = '{:d},{:d}'.format(result.coverage_ref, altCoverage)
            next_row_call_values = [result.genotype.label.encode('ascii', errors='backslashreplace'),
                                    next_row_call_allelicDepth,
                                    result.read_depth,
                                    result.genotype_quality]
            next_row.samples.append(vcf.model._Call(next_row, sample.label, row_call_format(*next_row_call_values)))
        for next_row in rows.itervalues():
            writer.write_record(next_row)
