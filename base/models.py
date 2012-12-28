from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User

class News(models.Model):
    title = models.CharField(max_length=1024, name=_('Title'))
    contents = models.TextField(name=_('Contents'))
    creation_time = models.DateTimeField(auto_now_add=True, name=_('Creation time'))
    created_by = models.ForeignKey(User, blank=True, null=True, default=None, related_name="created_news", name=_('Created by'))
    deleted = models.BooleanField(default=False, name=_('Deleted'))
    deleted_by = models.ForeignKey(User, blank=True, null=True, default=None, related_name="deleted_news", name=_('Deleted by'))
    deletion_time = models.DateTimeField(blank=True, null=True, name=_('Deletion time'))
    
    def __unicode__(self):
        return self.title

    class Admin:
        search_fields = ['title']
    
    class Meta:
        verbose_name = _('news')
        verbose_name_plural = _('news')
