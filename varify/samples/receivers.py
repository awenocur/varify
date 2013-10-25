import logging
from django.conf import settings
from django.contrib.auth.models import Group
from django.core.mail import send_mail
from django.db import transaction
from django.db.models.signals import post_save, post_delete
from guardian.shortcuts import assign
from .models import Cohort, Project, Batch, Sample

PROJECT_GROUP_TEMPLATE = '{} Project Team'
AUTO_PUBLISH_BATCH = getattr(settings, 'VARIFY_AUTO_PUBLISH_BATCH', True)

log = logging.getLogger(__name__)

@transaction.commit_on_success
def update_sample_for_autocreated_cohorts(instance, created, **kwargs):
    "Manages adding/removing samples from autocreated cohorts."
    # World
    lookup = {'batch': None, 'project': None, 'autocreated': True, 'name': 'World'}
    try:
        world_cohort = Cohort.objects.get(**lookup)
    except Cohort.DoesNotExist:
        world_cohort = Cohort(**lookup)
        world_cohort.save()

    project = instance.project

    # Project
    lookup = {'batch': None, 'project': project, 'autocreated': True}
    try:
        project_cohort = Cohort.objects.get(**lookup)
    except Cohort.DoesNotExist:
        project_cohort = Cohort(name=unicode(project), **lookup)
        project_cohort.save()

    if instance.published:
        world_cohort.add(instance, added=False)
        project_cohort.add(instance, added=False)
    else:
        world_cohort.remove(instance, delete=True)
        project_cohort.remove(instance, delete=True)


@transaction.commit_on_success
def auto_delete_cohort(instance, **kwargs):
    "Deletes and auto-created cohort named after the instance."
    cohorts = Cohort.objects.filter(autocreated=True)

    if isinstance(instance, Project):
        cohorts = cohorts.filter(project=instance)
    elif isinstance(instance, Batch):
        cohorts = cohorts.filter(batch=instance)
    else:
        return

    count = cohorts.count()
    cohorts.delete()
    log.info('Delete {0} autocreated cohorts for {1}'.format(count, instance))


def auto_create_project_group(instance, created, **kwargs):
    name = PROJECT_GROUP_TEMPLATE.format(instance.name)
    group, created = Group.objects.get_or_create(name=name)

    # TODO change this to queue up an email rather than doing it in process..
    if created:
        assign('view_project', group, instance)
        kwargs = {
            'subject': '{}Project "{}" Created'.format(settings.EMAIL_SUBJECT_PREFIX, name),
            'message': 'The "{}" Project Group has been created. This is a ' \
                'reminder to setup any permissions for the associated ' \
                'users.'.format(name),
            'from_email': settings.NO_REPLY_EMAIL,
            'recipient_list': [settings.SUPPORT_EMAIL],
        }
        send_mail(**kwargs)
        log.info('Autocreate project group {}'.format(group))


def auto_delete_project_group(instance, **kwargs):
    name = PROJECT_GROUP_TEMPLATE.format(instance.name)
    Group.objects.filter(name=name).delete()
    log.info('Delete autocreated project group {}'.format(name))


def update_batch_count(instance, **kwargs):
    """Sample post-save handler to update the sample's batch count.

    Batches are unpublished by default (to prevent publishing empty batches).
    If the `AUTO_PUBLISH_BATCH` setting is true, the batch will be published
    automatically when at least one published sample is in the batch.
    """
    batch = instance.batch
    count = batch.samples.filter(published=True).count()

    if count != batch.count:
        batch.count = count
        if AUTO_PUBLISH_BATCH:
            batch.published = bool(count)
        batch.save()


post_save.connect(update_sample_for_autocreated_cohorts, sender=Sample)
post_save.connect(update_batch_count, sender=Sample)
post_save.connect(auto_create_project_group, sender=Project)

post_delete.connect(auto_delete_cohort, sender=Batch)
post_delete.connect(auto_delete_cohort, sender=Project)