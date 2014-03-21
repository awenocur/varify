import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'varify.conf.settings')

from varify.variants.models import Variant
from varify.samples.models import Sample
from varify.samples.models import Result


selectedVariants = Sample.objects.get(id=1)
selectedVariants.variants.all()

print selectedVariants.variants.all()
