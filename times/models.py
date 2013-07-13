from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from curia import get_content_object
from django.utils.encoding import smart_unicode
from datetime import datetime

class Time(models.Model):
    user = models.ForeignKey(User, null=True, verbose_name=_('User'))
    content_type = models.ForeignKey(ContentType, verbose_name=_('Content type'))
    object_id = models.IntegerField(verbose_name=_('Object ID'))
    last_viewed = models.DateTimeField(verbose_name=_('Last viewed'), default=datetime(1900, 01, 01))
    bookmark = models.BooleanField(default=False, verbose_name=_('Bookmark'))
    
    def __unicode__(self):
        if self.user is None:
            return u'%s %s: %s' % (get_content_object(self), self.object_id, self.last_viewed)
        else:
            return u'%s %s %s: %s' % (get_content_object(self), self.object_id, self.user, self.last_viewed)
    
    def get_absolute_url(self):
        return get_content_object(self).get_absolute_url()
        
    def __lt__(self, obj):
        return self.last_viewed < obj.last_viewed
    
    def __gt__(self, obj):
        return self.last_viewed > obj.last_viewed
    
    def __eq__(self, obj):
        return self.last_viewed == obj.last_viewed

    class Meta:
        unique_together = (('user', 'content_type', 'object_id'),)
        verbose_name = _('time')
        verbose_name_plural = _('times')
        
    class Admin:
        search_fields = ['user__username']