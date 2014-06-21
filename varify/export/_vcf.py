# VCF exporter
# The primary purpose of this exporter is not to generate verbatim copies of
# VCF entries loaded into the db, but to use VCF as a common format that
# integrates into a bioinformatics workflow.  This exporter works with a client
# currently hosted at http://github.research.chop.edu/wenocur/varify_client

import time
import json
import textwrap
import logging
import vcf
from cStringIO import StringIO
from django.db.models import Q
from avocado.export._base import BaseExporter
from varify.variants.models import Variant
from varify.samples.models import Result

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
        vcf_file_header = textwrap.dedent('''\
            ##fileformat=VCFv4.1
            ##fileDate= ''') + time.strftime("%Y%m%d") + textwrap.dedent('''\
            ##source=''') + request.get_host() + textwrap.dedent('''\
            ##reference=GRCh37
            ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
            ##FORMAT=<ID=AD,Number=.,Type=Integer,Description="Allelic depths for the ref and alt alleles in the order listed">
            ##FORMAT=<ID=DP,Number=1,Type=Integer,Description="Approximate read depth (reads with MQ=255 or with bad mates are filtered)">
            ##FORMAT=<ID=GQ,Number=1,Type=Float,Description="Genotype Quality">
            #CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT'
        ''')  # noqa
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
            range_dicts = None
            # three ordered lists that correspond to the ranges above
            chromosomes = []
            beginning_bp = []
            ending_bp = []

            # chromosome ranges are optional
            if 'ranges' in data:
                range_dicts = data['ranges']
            # TODO: catch invalid/missing entries in the following dicts:
            if range_dicts:
                for dict in range_dicts:
                    chromosomes.append(str(dict["chrom"]))
                    beginning_bp.append(int(dict["start"]))
                    ending_bp.append(int(dict["end"]))

        # The following is an ORM-based implementation that works for now;
        # this should be migrated to use Avocado if possible
            # start with a QuerySet for all results
            all_results = Result.objects.get_query_set()
            # these shall be Q objects
            label_criteria = None
            range_criteria = None

            # take the union of all sets matching sample labels in the labels
            # array; store the predicate as a Q object
            for next_label in labels:
                next_criterion = Q(sample__label=next_label)
                if label_criteria is None:
                    label_criteria = next_criterion
                else:
                    label_criteria |= next_criterion

            # take the union of all sets matching ranges in the 3 corresponding
            # arrays; store the predicate as a Q object
            for chr, start, end in zip(chromosomes, beginning_bp, ending_bp):
                next_criterion = Q(variant__chr__label=chr) & Q(
                    variant__pos__lt=end + 1) & Q(
                    variant__pos__gt=start - 1)
                if range_criteria is None:
                    range_criteria = next_criterion
                else:
                    range_criteria |= next_criterion

            # if no ranges were provided, use a dummy Q object
            if range_criteria is None:
                range_criteria = Q()

            # grab the results, finally; take the intersection of the two Q
            # objects defined above, sort by the order defined in the VCF v4
            # specification
            selected_results = all_results.prefetch_related(
                'sample', 'variant').prefetch_related(
                'variant__chr').filter(
                label_criteria).filter(
                range_criteria).order_by(
                'variant__chr__order', 'variant__pos')

            # dict of rows in the VCF file; this is used to look up rows that
            # were already created, to aggregate samples by variant;
            # each row represents one variant
            rows = {}

            # VCF rows in the proper order, defined by the DBMS sorting by
            # variant positon
            ordered_rows = []

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
            sample_indexes = {}
            # keep track of the number of samples detected
            sample_num = 0
            # loop over all Results returned
            for result in selected_results:
                # this sample may or may not be the first for a particular
                # variant
                sample = result.sample
                # PyVCF uses ASCII, sorry; here's where we check whether we're
                # already handling a particular sample; if we're not, assign
                # it an index
                if sample.label.encode('ascii', errors='backslashreplace')\
                        not in sample_indexes:
                    sample_indexes[
                        sample.label.encode(
                            'ascii', errors='backslashreplace')] = sample_num
                    sample_num += 1
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
                        sample_indexes=sample_indexes,
                        samples=[])
                    # make it known that this variant has a PyVCF record
                    rows[variant.id] = next_row
                    # the order of rows as retrieved from the DB should be
                    # right for the VCF
                    ordered_rows.append(next_row)
                # hack to replace NULLs in the DB with zero where appropriate
                ref_coverage = 0
                if result.coverage_ref:
                    ref_coverage = result.coverage_ref
                alt_coverage = 0
                if result.coverage_alt:
                    alt_coverage = result.coverage_alt
                # populate the allelic depth field for a particular call
                next_row_call_allelicDepth = '{:d},{:d}'.format(
                    ref_coverage, alt_coverage)
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
                if(label in sample_indexes):
                    sample_indexes[label] = i
                    i += 1

            # prepare string for sample headers
            just_sample_indexes = sample_indexes.values()
            just_sample_names = sample_indexes.keys()
            sorted_sample_names = zip(*sorted(zip(just_sample_indexes,
                                                just_sample_names)))[1]
            template_sample_string = '\t' + '\t'.join(sorted_sample_names)

            # create a VCF writer based on a programmatically generated
            # template
            fake_template_file = StringIO(vcf_file_header +
                                          template_sample_string)
            template_reader = vcf.Reader(fake_template_file)
            writer = vcf.Writer(buff, template_reader)
            fake_template_file.close()

            # add nulls to replace missing calls; this is necessary for
            # variants not called for all samples in the VCF; this should
            # really be done
            # by PyVCF
            for next_row in ordered_rows:
                remaining_sample_labels = sample_indexes.keys()
                if len(next_row.samples) < len(remaining_sample_labels):
                    for next_sample in next_row.samples:
                        remaining_sample_labels.remove(next_sample.sample)
                    for next_label in remaining_sample_labels:
                        next_row.samples.append(
                            vcf.model._Call(
                                next_row, next_label,
                                row_call_format(None, None, None, None)))

                # The following code really should be part of PyVCF:
                # sorting the calls within the row:
                reordered_samples = [None] * len(next_row.samples)
                for call in next_row.samples:
                    index = next_row._sample_indexes[call.sample]
                    # the following line checks for an exceptional condition
                    # this should be handled in a later version of Varify
                    # rather than being thrown, and should not be added
                    # to PyVCF
                    assert reordered_samples[index] is None
                    reordered_samples[index] = call
                next_row.samples = reordered_samples

                writer.write_record(next_row)
            writer.close()

        # junk code to make the VCF export option from the UI generate
        # something
        else:
            fake_template_file = StringIO(self.vcf_file_header)
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
                selected_variant = Variant.objects.get(pk=variant_id)
                next_row = vcf.model._Record(ID=variant_id,
                                             CHROM=selected_variant.chr,
                                             POS=selected_variant.pos,
                                             REF=selected_variant.ref,
                                             ALT=selected_variant.alt,
                                             # replace the following stubs:
                                             QUAL=0, FILTER=None,
                                             INFO=None, FORMAT=None,
                                             sample_indexes=None,
                                             samples=None)
                writer.write_record(next_row)
        return buff
