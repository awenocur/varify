# VCF exporter
# The primary purpose of this exporter is not to generate verbatim copies of
# VCF entries loaded into the db, but to use VCF as a common format that
# integrates into a bioinformatics workflow.  This exporter works with a client
# currently hosted at http://github.research.chop.edu/wenocur/varify_client

import logging
import vcf
from avocado.export._base import BaseExporter
from varify.variants.models import Variant
from varify.samples.models import Result
from django.db.models import Q
import json
from StringIO import StringIO
import time

log = logging.getLogger(__name__)


class VcfExporter(BaseExporter):
    short_name = 'VCF'
    long_name = 'Variant Call Format'

    file_extension = 'vcf'
    content_type = 'text/variant-call-format'

    def write(self, iterable, buff=None, *args, **kwargs):
        header = []
        request = kwargs['request']
        # descriptions of the fields currently supported by the exporter;
        # this is to be prepended to the actual header, describing lines
        VcfFileHeader =\
            '##fileformat=VCFv4.1\n'\
            '##fileDate=' + time.strftime("%Y%m%d") + \
            '\n##source=' + request.get_host() + \
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

        # Eventually, POST and GET should be handled by the same code;
        # GET shall require info that's not always provided by the iterable;
        # POST should ignore the iterable by design, since it interfaces with
        # a dedicated client
        if request.method == 'POST':
            # decode the parameters passed from the client
            data = json.load(request._stream)
            # get the list of sample labels
            labels = data['samples']
            # dictionaries encoded by the client to store chromosome ranges
            rangeDicts = None
            # three ordered lists that correspond to the ranges above
            chromosomes = []
            beginningBp = []
            endingBp = []

            # chromosome ranges are optional
            if 'ranges' in data:
                rangeDicts = data['ranges']
            # TODO: catch invalid/missing entries in the following dicts:
            if rangeDicts:
                for dict in rangeDicts:
                    chromosomes.append(str(dict["chrom"]))
                    beginningBp.append(int(dict["start"]))
                    endingBp.append(int(dict["end"]))

        # The following is an ORM-based implementation that works for now;
        # this should be migrated to use Avocado if possible
            # start with a QuerySet for all results
            allResults = Result.objects.get_query_set()
            # these shall be Q objects
            labelCriteria = None
            rangeCriteria = None

            # take the union of all sets matching sample labels in the labels
            # array; store the predicate as a Q object
            for nextLabel in labels:
                nextCriterion = Q(sample__label=nextLabel)
                if labelCriteria is None:
                    labelCriteria = nextCriterion
                else:
                    labelCriteria |= nextCriterion

            # take the union of all sets matching ranges in the 3 corresponding
            # arrays; store the predicate as a Q object
            for chr, start, end in zip(chromosomes, beginningBp, endingBp):
                nextCriterion = Q(variant__chr__label=chr) & Q(
                    variant__pos__lt=end + 1) & Q(
                    variant__pos__gt=start - 1)
                if rangeCriteria is None:
                    rangeCriteria = nextCriterion
                else:
                    rangeCriteria |= nextCriterion

            # if no ranges were provided, use a dummy Q object
            if rangeCriteria is None:
                rangeCriteria = Q()

            # grab the results, finally; take the intersection of the two Q
            # objects defined above, sort by the order defined in the VCF v4
            # specification
            selectedResults = allResults.prefetch_related(
                'sample', 'variant').prefetch_related(
                'variant__chr').filter(
                labelCriteria).filter(
                rangeCriteria).order_by(
                'variant__chr__order', 'variant__pos')

            # dict of rows in the VCF file; this is used to look up rows that
            # were already created, to aggregate samples by variant;
            # each row represents one variant
            rows = {}

            # VCF rows in the proper order, defined by the DBMS sorting by
            # variant positon
            orderedRows = []

            # this is something pyVCF needs to know how the call is formatted;
            # each sample listed in a row has sub-columns in this order
            # pyVCF requires this info to be declared again a different way
            row_call_format = vcf.model.make_calldata_tuple(['GT',
                                                             'AD',
                                                             'DP',
                                                             'GQ'])
            # data types for the fields declared on the prior line
            row_call_format._types.append('String')
            row_call_format._types.append('String')
            row_call_format._types.append('Integer')
            row_call_format._types.append('Integer')
            # lookup dict for sample indexes; this is linked to each PyVCF
            # Record object
            sampleIndexes = {}
            # keep track of the number of samples detected
            sampleNum = 0
            # loop over all Results returned
            for result in selectedResults:
                # this sample may or may not be the first for a particular
                # variant
                sample = result.sample
                # PyVCF uses ASCII, sorry; here's where we check whether we're
                # already handling a particular sample; if we're not, assign
                # it an index
                if sample.label.encode('ascii', errors='backslashreplace')\
                        not in sampleIndexes:
                    sampleIndexes[
                        sample.label.encode(
                            'ascii', errors='backslashreplace')] = sampleNum
                    sampleNum += 1
                variant = result.variant
                # here's where we check whether we're already handling a
                # particular variant; if we're not, create a new PyVCF record
                if variant.id in rows:
                    next_row = rows[variant.id]
                else:
                    rsid = variant.rsid
                    if rsid:
                        rsid = rsid.encode('ascii', errors='backslashreplace')
                    # we haven't seen this variant before, create a new record
                    next_row = vcf.model._Record(
                        ID=rsid,
                        CHROM=variant.chr.label,
                        POS=variant.pos,
                        REF=variant.ref,
                        ALT=variant.alt,
                        QUAL=result.quality,
                        FILTER=None,
                        # here's where the call format is specified
                        # a second time, as required by PyVCF
                        INFO=None, FORMAT='GT:AD:DP:GQ',
                        sample_indexes=sampleIndexes,
                        samples=[])
                    # make it known that this variant has a PyVCF record
                    rows[variant.id] = next_row
                    # the order of rows as retrieved from the DB should be
                    # right for the VCF
                    orderedRows.append(next_row)
                # hack to replace NULLs in the DB with zero where appropriate
                refCoverage = 0
                if result.coverage_ref:
                    refCoverage = result.coverage_ref
                altCoverage = 0
                if result.coverage_alt:
                    altCoverage = result.coverage_alt
                # populate the allelic depth field for a particular call
                next_row_call_allelicDepth = '{:d},{:d}'.format(
                    refCoverage, altCoverage)
                # generate call values array for PyVCF
                next_row_call_values = [result.genotype.value.encode(
                    'ascii', errors='backslashreplace'),
                    next_row_call_allelicDepth,
                    result.read_depth,
                    result.genotype_quality]
                # add call to its corresponding PyVCF record
                next_row.samples.append(
                    vcf.model._Call(next_row, sample.label,
                                    row_call_format(*next_row_call_values)))

            # sort samples as they are found on the command line
            i = 0
            for label in labels:
                if(label in sampleIndexes):
                    sampleIndexes[label] = i
                    i += 1

            # prepare string for sample headers
            justSampleIndexes = sampleIndexes.values()
            justSampleNames = sampleIndexes.keys()
            sortedSampleNames = zip(*sorted(zip(justSampleIndexes,
                                                justSampleNames)))[1]
            templateSampleString = '\t' + '\t'.join(sortedSampleNames)

            # create a VCF writer based on a programmatically generated
            # template
            fake_template_file = StringIO(VcfFileHeader +
                                          templateSampleString)
            template_reader = vcf.Reader(fake_template_file)
            writer = vcf.Writer(buff, template_reader)
            fake_template_file.close()

            # add nulls to replace missing calls; this is necessary for
            # variants not called for all samples in the VCF; this should
            # really be done
            # by PyVCF
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

                # The following code really should be part of PyVCF:
                # sorting the calls within the row:
                reorderedSamples = [None] * len(next_row.samples)
                for call in next_row.samples:
                    index = next_row._sample_indexes[call.sample]
                    # the following line checks for an exceptional condition
                    # this should be handled in a later version of Varify
                    # rather than being thrown, and should not be added
                    # to PyVCF
                    assert reorderedSamples[index] is None
                    reorderedSamples[index] = call
                next_row.samples = reorderedSamples

                writer.write_record(next_row)
            writer.close()

        # junk code to make the VCF export option from the UI generate
        # something
        else:
            fake_template_file = StringIO(self.VcfFileHeader)
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
                                             # replace the following stubs:
                                             QUAL=0, FILTER=None,
                                             INFO=None, FORMAT=None,
                                             sample_indexes=None,
                                             samples=None)
                writer.write_record(next_row)
        return buff
