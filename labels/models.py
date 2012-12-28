from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User, Group
from curia.notifications import enable_notifications

class Label(models.Model):
    name = models.CharField(max_length=100, name=_('Name'))
    content_type = models.ForeignKey(ContentType, name=_('Content type'))
    object_id = models.IntegerField(_('Object ID'), name=_('Object ID'))
    owner_user = models.ForeignKey(User, blank=True, null=True, verbose_name=_('Owner user'), related_name="labels_on_owned_objects", name=_('owner user'), editable=False) # duplicates data from the target object to help filtering
    owner_group = models.ForeignKey(Group, blank=True, null=True, verbose_name=_('Owner group'), related_name="labels_on_owned_objects", name=_('owner group'), editable=False) # duplicates data from the target object to help filtering
    created_by = models.ForeignKey(User, blank=True, null=True, default=None, related_name="labels_added", name=_('Created by'))
    creation_time = models.DateTimeField(auto_now_add=True, name=_('Creation time'))
    deleted = models.BooleanField(default=False, name=_('Deleted'))
    deleted_by = models.ForeignKey(User, blank=True, null=True, default=None, related_name="deleted_labels", name=_('Deleted by'))
    deletion_time = models.DateTimeField(blank=True, null=True, name=_('Deletion time'))

    def save(self, force_insert=False, using=None):
        obj = self.get_corresponding_object()
        if hasattr(obj, 'owner_user'):
            if obj.owner_user != None:
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
    group = models.ForeignKey(Group, name=_('Group'))
    title = models.CharField(max_length=1024, name=_('Title'))
    label = models.CharField(max_length=1024, name=_('Label'))
    content_type = models.ForeignKey(ContentType, name=_('Content type'))
    creation_time = models.DateTimeField(auto_now_add=True, name=_('Creation time'))
    created_by = models.ForeignKey(User, blank=True, null=True, default=None, related_name="created_suggested_labels", name=_('Created by'))
    deleted = models.BooleanField(default=False, name=_('Deleted'))
    deleted_by = models.ForeignKey(User, blank=True, null=True, default=None, related_name="deleted_suggested_labels", name=_('Deleted by'))
    deletion_time = models.DateTimeField(blank=True, null=True, name=_('Deletion time'))
    
    def __unicode__(self):
        return self.title
    
    def get_absolute_url(self):
        return '/%s/groups/%s/?search=%s' % (self.content_type, self.group.id, self.label)
    
    class Admin:
        search_fields = ['title', 'label']
    
    class Meta:
        verbose_name = _('suggested label')
        verbose_name_plural = _('suggested labels')
