import os
from django.core.cache import cache
from django.core import management
from django.test import TestCase
from django.contrib.auth.models import User
from django_rq import get_queue, get_connection
from rq.queue import get_failed_queue
from django.test.utils import override_settings
from django_rq import get_worker

TESTS_DIR = os.path.join(os.path.dirname(__file__), '../..')
SAMPLE_DIRS = [os.path.join(TESTS_DIR, 'samples')]

@override_settings(VARIFY_SAMPLE_DIRS=SAMPLE_DIRS)
class dummyTestCase2(TestCase):

    def setUp(self):
        print "dummy2 begin setUp"
        cache.clear()
        get_queue('variants').empty()
        get_queue('default').empty()
        get_failed_queue(get_connection()).empty()
        self.user = User.objects.create_user(username='test', password='test')
        print "dummy2 end setUp"

    def test_dummy(self):
        print "dummy2 begin test"
        worker1 = get_worker('variants')
        worker2 = get_worker('default')
        management.call_command('samples', 'queue')

        worker1.work(burst=True)
        worker2.work(burst=True)

        self.assertTrue(True, "This should be true!")
        print "dummy2 end test"

    def tearDown(self):
        print "dummy2 begin tearDown"
        super(self, dummyTestCase2).tearDown()
        print "dummy2 end tearDown"