from django.db import models
from django.contrib.auth.models import User,Group
from django.conf import settings
from django.db.models import signals
from django.dispatch import dispatcher
from django.utils.translation import ugettext_lazy as _
from curia.notifications import enable_notifications
import os

class File(models.Model):
    file = models.FileField(upload_to='files', blank=True, name=_('File'))
    title = models.CharField(max_length=1024, name=_('Title'))
    owner_user = models.ForeignKey(User, blank=True, null=True, verbose_name=_('Owner user'), name=_('owner user'))
    owner_group = models.ForeignKey(Group, blank=True, null=True, verbose_name=_('Owner group'), name=_('owner group'))
    creation_time = models.DateTimeField(auto_now_add=True, name=_('Creation time'))
    description = models.TextField(blank=True, name=_('Description'))
    deleted = models.BooleanField(default=False, name=_('Deleted'))
    deleted_by = models.ForeignKey(User, blank=True, null=True, default=None, related_name="deleted_files", name=_('Deleted by'))
    deletion_time = models.DateTimeField(blank=True, null=True, name=_('Deletion time'))
    
    def __unicode__(self):
        return self.title

    def save(self, force_insert=False, using=None):
        if self.owner_user is None and self.owner_group is None:
            raise ValueError('A thread must be owned by a user or a group.')
    
        models.Model.save(self, force_insert, using=using)
    
    class Admin:
        search_fields = ['description']
 
    class Meta:
        verbose_name = _('file')
        verbose_name_plural = _('files')    
 
enable_notifications(File)