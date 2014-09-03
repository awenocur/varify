from itertools import compress
import vcf

class TestParser(object):
    samples = None
    records = []
    test_case = None

    def __init__(self, buffer, test_case):
        stream = vcf.Reader(buffer)
        self.samples = stream.samples
        self.test_case = test_case
        self.records = []
        while True:
            try:
                record = next(stream)
                self.records.append(record)
            except StopIteration:
                break

    def check_samples(self, samples):
        for my_sample, other_sample in zip(self.samples, samples,):
            self.test_case.assertTrue(my_sample == other_sample)

    def check_unordered_samples(self, samples):
        for other_sample in samples:
            self.test_case.assertTrue(other_sample in self.samples)

    def check_info(self, field_name, record_number, value):
        record = self.records[record_number]
        my_value = record.INFO.get(field_name)
        self.test_case.assertTrue(value == my_value)

    def check_multi_field(self, sample_name, record_number, *args):
        """
        pass in sample name, record number, followed by alternating list of
        keys and values
        """
        my_data = self.records[record_number].genotype(sample_name).data
        for key, value in zip (compress(args, [1, 0]*(len(args)/2)),
                         compress(args, [0, 1]*(len(args)/2))):
            self.test_case.assertEqual(getattr(my_data, key), value)

    def check_multi_info(self, field_name, record_number, values):
        record = self.records[record_number]
        my_values = record.INFO.get(field_name)
        for value in values:
            self.test_case.assertTrue(value in my_values)

    def check_num_records(self, num):
        self.test_case.assertEqual(len(self.records), num)
