import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'varify.conf.settings')

from varify.variants.models import Variant
from varify.samples.models import Sample
from varify.samples.models import Result


selectedSamples = Sample.objects.filter(label='NA12891').select_related('variant')
for sample in selectedSamples:
    print sample.variants.all()
