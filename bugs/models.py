from django.db import models
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext_lazy as _

class Bug(models.Model):
    description = models.TextField(verbose_name=_('Description'))
    reporter = models.ForeignKey(User, verbose_name=_('Reporter'))
    creation_time = models.DateTimeField(auto_now_add=True, verbose_name=_('Creation time'))
    urls = models.TextField(blank=True, verbose_name=_('URLs'))
    browser = models.CharField(max_length=767, verbose_name=_('Browser'))

    deleted = models.BooleanField(default=False, verbose_name=_('Deleted'))
    deleted_by = models.ForeignKey(User, blank=True, null=True, default=None, related_name="deleted_bugs", verbose_name=_('Deleted by'))
    deletion_time = models.DateTimeField(blank=True, null=True, verbose_name=_('Deletion time'))
    deleted_reason = models.CharField(max_length=767, blank=True, null=True, verbose_name=_('Deletion reason'))
    
    #def get_absolute_url(self):
        #return '/bugs/%s/' % self.id
    
    class Admin:
        pass
        
    def __unicode__(self):
        return unicode(self.reporter)+': '+self.description[0:20]