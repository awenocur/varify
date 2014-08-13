import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'varify.conf.settings')

from varify.variants.models import Variant
from varify.samples.models import Sample
from varify.samples.models import Result
from django.db.models import Q


allSamples = Sample.objects.get_query_set()
labelCriteria = None
nextCriterion = Q(label='NA12891')
if labelCriteria == None:
    labelCriteria = nextCriterion
else:
    labelCriteria |= nextCriterion
selectedSamples = allSamples.filter(labelCriteria).select_related('variant')
for sample in selectedSamples:
    for variant in sample.variants.all():
        print variant
