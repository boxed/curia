from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User, Group
from curia.notifications import enable_notifications

class Label(models.Model):
    name = models.CharField(max_length=100, verbose_name=_('Name'))
    content_type = models.ForeignKey(ContentType, verbose_name=_('Content type'))
    object_id = models.IntegerField(verbose_name=_('Object ID'))
    owner_user = models.ForeignKey(User, blank=True, null=True, verbose_name=_('Owner user'), related_name="labels_on_owned_objects", editable=False) # duplicates data from the target object to help filtering
    owner_group = models.ForeignKey(Group, blank=True, null=True, verbose_name=_('Owner group'), related_name="labels_on_owned_objects", editable=False) # duplicates data from the target object to help filtering
    created_by = models.ForeignKey(User, blank=True, null=True, default=None, related_name="labels_added", verbose_name=_('Created by'))
    creation_time = models.DateTimeField(auto_now_add=True, verbose_name=_('Creation time'))
    deleted = models.BooleanField(default=False, verbose_name=_('Deleted'))
    deleted_by = models.ForeignKey(User, blank=True, null=True, default=None, related_name="deleted_labels", verbose_name=_('Deleted by'))
    deletion_time = models.DateTimeField(blank=True, null=True, verbose_name=_('Deletion time'))

    def save(self, force_insert=False, using=None):
        obj = self.get_corresponding_object()
        if hasattr(obj, 'owner_user'):
            if obj.owner_user is not None:
                self.owner_user = obj.owner_user
            else:
                self.owner_group = obj.owner_group
        elif hasattr(obj, 'owner'):
            self.owner_user = obj.owner

        models.Model.save(self, force_insert=force_insert, using=using)

    class Admin:
        search_fields = ['name']

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return '/labels/%s/' % self.name

    def get_corresponding_object(self):
        return self.content_type.get_object_for_this_type(pk=self.object_id)

    class Meta:
        verbose_name = _('label')
        verbose_name_plural = _('labels')

enable_notifications(Label)
class SuggestedLabel(models.Model):
    group = models.ForeignKey(Group, verbose_name=_('Group'))
    title = models.CharField(max_length=1024, verbose_name=_('Title'))
    label = models.CharField(max_length=1024, verbose_name=_('Label'))
    content_type = models.ForeignKey(ContentType, verbose_name=_('Content type'))
    creation_time = models.DateTimeField(auto_now_add=True, verbose_name=_('Creation time'))
    created_by = models.ForeignKey(User, blank=True, null=True, default=None, related_name="created_suggested_labels", verbose_name=_('Created by'))
    deleted = models.BooleanField(default=False, verbose_name=_('Deleted'))
    deleted_by = models.ForeignKey(User, blank=True, null=True, default=None, related_name="deleted_suggested_labels", verbose_name=_('Deleted by'))
    deletion_time = models.DateTimeField(blank=True, null=True, verbose_name=_('Deletion time'))

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return '/%s/groups/%s/?search=%s' % (self.content_type, self.group.id, self.label)

    class Admin:
        search_fields = ['title', 'label']

    class Meta:
        verbose_name = _('suggested label')
        verbose_name_plural = _('suggested labels')
