from django.db import models
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import gettext
from curia import get_content_object
from django.utils.encoding import smart_unicode
from datetime import datetime

class Watcher(models.Model):
    user = models.ForeignKey(User, related_name='watchers', verbose_name=_('User'))
    content_type = models.ForeignKey(ContentType, null=True, blank=True, verbose_name=_('Content type'))
    object_id = models.IntegerField(null=True, blank=True, verbose_name=_('Object ID'))
    owner_user = models.ForeignKey(User, null=True, blank=True, related_name='registered_watchers', verbose_name=_('Owner user'))
    owner_group = models.ForeignKey(Group, null=True, blank=True, related_name='registered_watchers', verbose_name=_('Owner group'))
    inverse = models.BooleanField(default=False, verbose_name=_('Negate'))
    
    def __unicode__(self):
        return smart_unicode(self.user)+u': '+smart_unicode(self.short_description())
        
    def short_description(self):
        if self.content_type != None:
            result = self.content_type.model_class()._meta.verbose_name.lower()+': '
        else:
            result = 'None: '
        if self.inverse:
            result += gettext('not ')
        try:
            if self.object_id:
                result += smart_unicode(get_content_object(self))
            else:
                if self.content_type:
                    result += gettext('all ')+smart_unicode(self.content_type)+'s'
                else:
                    result += gettext('everything ')                    
        except AttributeError:
            pass
        
        #if result != '':
        #    result += smart_unicode(gettext(' for '))
        #if self.owner_user:
        #    result += smart_unicode(gettext('user'))+u' '+smart_unicode(self.owner_user)
        #elif self.owner_group:
        #    result += smart_unicode(gettext('group'))+u' '+smart_unicode(self.owner_group)
        #else:
        #    result += _('myself')
        
        return result
        
    def get_absolute_url(self):
        if self.object_id == None:
            if self.content_type == None:
                if self.owner_user == None:
                    return self.owner_group.get_absolute_url()
                else:
                    return self.owner_user.get_absolute_url()
            else:
                if self.owner_user == None:
                    return '/%ss/groups/%s/' % (self.content_type, self.owner_group.id)
                else:
                    return '/%ss/users/%s/' % (self.content_type, self.owner_user.id)
                
        else:
            return get_content_object(self).get_absolute_url()

    def save(self, force_insert=False, using=None):
        if self.owner_user is not None and self.owner_group is not None:
            self.owner_user = None#raise ValueError('A watcher may not be set on both a user and a group at the same time.') 

        models.Model.save(self, force_insert, using=using)
    
    class Admin:
        search_fields = ['user__username']
        
    class Meta:
        unique_together = (('user', 'content_type', 'object_id'),)
        verbose_name = _('watcher')
        verbose_name_plural = _('watchers')
        
class Notification(models.Model):
    user = models.ForeignKey(User, verbose_name=_('User'))
    content_type = models.ForeignKey(ContentType, verbose_name=_('Content type'))
    object_id = models.IntegerField(verbose_name=_('Object ID'))
    title = models.CharField(max_length=1024, verbose_name=_('Name'))
    url = models.CharField(max_length=1024, verbose_name=_('Url'))
    originator_user = models.ForeignKey(User, null=True, blank=True, related_name='generated_notifications', verbose_name=_('Owner user'))
    originator_group = models.ForeignKey(Group, null=True, blank=True, related_name='generated_notifications', verbose_name=_('Owner group'))
    
    def __unicode__(self):
        return self.title
    
    def get_absolute_url(self):
        if '?' in self.url:
            sep = '&'
        else:
            sep = '?'
        return '%s%shack=%s#firstnew' % (self.url, sep, datetime.now())

    class Admin:
        search_fields = ['user__username']
        
    class Meta:
        unique_together = (('user', 'content_type', 'object_id'),)
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')
        ordering = ('id',)
        
class Bookmark(models.Model):
    user = models.ForeignKey(User, related_name='bookmarks', verbose_name=_('User'))
    title = models.CharField(max_length=1024, verbose_name=_('Name'))
    url = models.CharField(max_length=1024, verbose_name=_('Url'))

    def __unicode__(self):
        return self.title
    
    def get_absolute_url(self):
        return self.url

    class Admin:
        search_fields = ['user__username']
        
    class Meta:
        verbose_name = _('Bookmark')
        verbose_name_plural = _('Bookmarks')
        ordering = ('title',)
        
class IgnoreLabel(models.Model):
    user = models.ForeignKey(User)
    label = models.CharField(max_length=100, verbose_name=_('Label'))
    
    def __unicode__(self):
        return '%s ignores %s' % (self.user, self.label)
    
    class Admin:
        pass
        
class SubscriptionResult(models.Model):
    user = models.ForeignKey(User)
    content_type = models.ForeignKey(ContentType, verbose_name=_('Content type'))
    object_id = models.IntegerField(verbose_name=_('Object ID'))
    originator_user = models.ForeignKey(User, null=True, blank=True, related_name='generated_subscription_results', verbose_name=_('Owner user'))
    originator_group = models.ForeignKey(Group, null=True, blank=True, related_name='generated_subscription_results', verbose_name=_('Owner group'))
    
    def __unicode__(self):
        return u'%s %s %s' % (self.user, self.content_type, self.object_id)
        
    class Admin:
        pass