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
from StringIO import StringIO

log = logging.getLogger(__name__)


class VcfExporter(BaseExporter):
    short_name = 'VCF'
    long_name = 'Variant Call Format'

    #descriptions of the fields currently supported by the exporter;
    #this is to be prepended to the actual header, describing lines

    file_extension = 'vcf'
    content_type = 'text/variant-call-format'

    def write(self, iterable, buff=None, *args, **kwargs):
        header = []
        request = kwargs['request']
        VcfFileHeader =\
            '##fileformat=VCFv4.1\n'\
            '##fileDate=20140613\n'\
            '##source=' + request.get_host() + \
            '\n##reference=GRCh37\n'\
            '##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">\n'\
            '##FORMAT=<ID=AD,Number=.,Type=Integer,Description="Allelic '\
                'depths for the ref and alt alleles in the order listed">\n'\
            '##FORMAT=<ID=DP,Number=1,Type=Integer,Description="Approximate'\
                ' read depth (reads with MQ=255 or with bad mates are '\
                'filtered)">\n'\
            '##FORMAT=<ID=GQ,Number=1,Type=Float,Description="Genotype '\
            'Quality">\n'\
            '#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT'
        buff = self.get_file_obj(buff)

        if request.method == 'POST':

            data = json.load(request._stream)

            labels = data['samples']

            rangeDicts = None
            chromosomes = []
            beginningBp = []
            endingBp = []

            if 'ranges' in data:
                rangeDicts = data['ranges'];
            #TODO: catch invalid/missing entries in the following dicts:
            if rangeDicts:
                for dict in rangeDicts:
                    chromosomes.append(str(dict["chrom"]))
                    beginningBp.append(int(dict["start"]))
                    endingBp.append(int(dict["end"]))

            allResults = Result.objects.get_query_set()
            labelCriteria = None
            rangeCriteria = None
            for nextLabel in labels:
                nextCriterion = Q(sample__label=nextLabel)
                if labelCriteria == None:
                    labelCriteria = nextCriterion
                else:
                    labelCriteria |= nextCriterion
            for chr, start, end in zip(chromosomes, beginningBp, endingBp):
                nextCriterion = Q(variant__chr__label = chr) & Q(
                    variant__pos__lt = end + 1) & Q(variant__pos__gt = start
                                                                       - 1)
                if rangeCriteria == None:
                    rangeCriteria = nextCriterion
                else:
                    rangeCriteria |= nextCriterion
            selectedResults = allResults.prefetch_related(
                'sample', 'variant').prefetch_related(
                'variant__chr').filter(
                labelCriteria).filter(
                rangeCriteria).order_by(
                'variant__chr__order', 'variant__pos')
            rows = {}
            orderedRows = []
            row_call_format = vcf.model.make_calldata_tuple(['GT',
                                                             'AD',
                                                             'DP',
                                                             'GQ'])
            row_call_format._types.append('String')
            row_call_format._types.append('String')
            row_call_format._types.append('Integer')
            row_call_format._types.append('Integer')
            sampleIndexes = {}
            sampleNum = 0
            for result in selectedResults:
                sample = result.sample
                if sample.label.encode('ascii', errors='backslashreplace')\
                        not in sampleIndexes:
                    sampleIndexes[
                        sample.label.encode(
                            'ascii', errors='backslashreplace')] = sampleNum
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
                refCoverage = 0
                if result.coverage_ref:
                    refCoverage = result.coverage_ref
                altCoverage = 0
                if result.coverage_alt:
                    altCoverage = result.coverage_alt
                next_row_call_allelicDepth = '{:d},{:d}'.format(
                    refCoverage, altCoverage)
                next_row_call_values = [result.genotype.value.encode(
                    'ascii', errors='backslashreplace'),
                                        next_row_call_allelicDepth,
                                        result.read_depth,
                                        result.genotype_quality]
                next_row.samples.append(
                    vcf.model._Call(next_row, sample.label,
                                    row_call_format(*next_row_call_values)))

            #prepare string for sample headers
            justSampleIndexes = sampleIndexes.values()
            justSampleNames = sampleIndexes.keys()
            sortedSampleNames = zip(*sorted(zip(justSampleIndexes,
                                                justSampleNames)))[1]
            templateSampleString = '\t' + '\t'.join(sortedSampleNames)

            #create a VCF writer based on a programmatically generated template
            fake_template_file=StringIO(VcfFileHeader +
                                        templateSampleString)
            template_reader = vcf.Reader(fake_template_file)
            writer = vcf.Writer(buff, template_reader)
            fake_template_file.close()

            #add nulls to replace missing calls; this is necessary for variants
            #not called for all samples in the VCF; this should really be done
            #by PyVCF
            for next_row in orderedRows:
                remainingSampleLabels = sampleIndexes.keys()
                if len(next_row.samples) < len(remainingSampleLabels):
                    for next_sample in next_row.samples:
                        remainingSampleLabels.remove(next_sample.sample)
                    for next_label in remainingSampleLabels:
                        next_row.samples.append(
                            vcf.model._Call(
                                next_row, next_label,
                                row_call_format(None, None, None, None)))

                #The following code really should be part of PyVCF:
                #sorting the calls within the row:
                reorderedSamples = [None] * len(next_row.samples)
                for call in next_row.samples:
                    index = next_row._sample_indexes[call.sample]
                    #the following line checks for an exceptional condition
                    #this should be handled in a later version of Varify
                    #rather than being thrown, and should not be added to PyVCF
                    assert reorderedSamples[index] == None
                    reorderedSamples[index] = call
                next_row.samples = reorderedSamples

                writer.write_record(next_row)

        else:
            fake_template_file=StringIO(self.VcfFileHeader)
            template_reader = vcf.Reader(fake_template_file)
            writer = vcf.Writer(buff, template_reader)
            fake_template_file.close()
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
