import os
from django.db import models
from django.db.models import signals
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import smart_unicode
from curia.notifications import enable_notifications
from curia import *

class Detail(models.Model):
    owner_user = models.ForeignKey(User, blank=True, null=True, related_name='user_details', verbose_name=_('User'))
    owner_group = models.ForeignKey(Group, blank=True, null=True, related_name='group_details', verbose_name=_('Group'))
    name = models.CharField(max_length=1024, verbose_name=_('Name'))
    value = models.TextField(blank=True, verbose_name=_('Value'))

    def __unicode__(self):
        if self.owner_user:
            return smart_unicode(self.owner_user)+' '+self.name+'='+self.value
        else:
            return smart_unicode(self.owner_group)+' '+self.name+'='+self.value

    class Admin:
        search_fields = ['user__username']
        
    class Meta:
        verbose_name = _('detail')
        verbose_name_plural = _('Details')
        ordering = ('id',)
        
class UserPermission(models.Model):
    user = models.ForeignKey(User, verbose_name=_('User'))
    command = models.CharField(verbose_name=_('Command'), max_length=50)
    content_type = models.ForeignKey(ContentType, verbose_name=_('Content type'))
    object_id = models.IntegerField(verbose_name=_('Object ID'))
    deny = models.BooleanField(default=False, verbose_name=_('Deny'))
    
    def __unicode__(self):
        if self.deny:
            return unicode(_('%(user)s is denied %(command)s access to %(content_type)s %(object_id)s')) % {'user':self.user, 'content_type':self.content_type, 'object_id':self.object_id, 'command':self.command}
        else:
            return unicode(_('%(user)s has %(command)s access to %(content_type)s %(object_id)s')) % {'user':self.user, 'content_type':self.content_type, 'object_id':self.object_id, 'command':self.command}
            
    def short_description(self):
        if self.deny:
            return _('%(user)s is denied access') % {'user':self.user}
        else:
            return _('%(user)s has access') % {'user':self.user}
    
    class Admin:
        search_fields = ['user__username']

    class Meta:
        ordering = ('-object_id',)
        verbose_name = _('user permission')
        verbose_name_plural = _('user permissions')
        
class GroupPermission(models.Model):
    group = models.ForeignKey(Group, verbose_name=_('Group'))
    command = models.CharField(verbose_name=_('Command'), max_length=50)
    content_type = models.ForeignKey(ContentType, verbose_name=_('Content type'))
    object_id = models.IntegerField(verbose_name=_('Object ID'))
    deny = models.BooleanField(default=False, verbose_name=_('Deny'))

    def __unicode__(self):
        if self.deny:
            return unicode(_('%(group)s is denied %(command)s access to %(content_type)s %(object_id)s')) % {'group':self.group, 'content_type':self.content_type, 'object_id':self.object_id, 'command':self.command}
        else:
            return unicode(_('%(group)s has %(command)s access to %(content_type)s %(object_id)s')) % {'group':self.group, 'content_type':self.content_type, 'object_id':self.object_id, 'command':self.command}

    def short_description(self):
        if self.deny:
            return unicode(_('%(group)s is denied access')) % {'group':self.group}
        else:
            return unicode(_('%(group)s has access')) % {'group':self.group}
    
    class Admin:
        search_fields = ['group__name']

    class Meta:
        ordering = ('-deny',)
        verbose_name = _('group permission')
        verbose_name_plural = _('group permissions')
    
class MetaUser(models.Model):
    Gender_Choices = (
        ('M', _('Male')),
        ('F', _('Female')),
    )
    
    NotificationStyle_Choices = (
        ('D', _('Default')),
        ('E', _('On every event')),
    )
    
    user = models.OneToOneField(User, primary_key=True, related_name='meta', verbose_name=_('User'))
    birthday = models.DateField(blank=True, null=True, verbose_name=_('Birthday'))
    picture = models.ImageField(upload_to='user-pictures',blank=True, verbose_name=_('Picture'))
    gender = models.CharField(verbose_name=_('Gender'), choices = Gender_Choices, max_length=10)
    location = models.CharField(verbose_name=_('Location'), max_length=200)
    inviter = models.ForeignKey(User, blank=True, null=True, related_name='invites', verbose_name=_('Inviter'))
    friends = models.ForeignKey(Group, related_name='friends_of', blank=True, null=True, verbose_name=_('Friends'))
    language = models.CharField(verbose_name=_('Language'), max_length=10)
    deleted_by = models.ForeignKey(User, blank=True, null=True, default=None, related_name='deleted_users', verbose_name=_('Deleted by'))
    deletion_time = models.DateTimeField(blank=True, null=True, verbose_name=_('Deletion time'))
    last_notification_email_time = models.DateTimeField(blank=True, null=True, verbose_name=_('Notification e-mail time'))
    notification_style = models.CharField(verbose_name=_('Notification Style'), choices = NotificationStyle_Choices, max_length=10, default='D')

    def presentation(self):
        try:
            from curia.documents.models import Document
            return Document.objects.get(owner_user=self.user, is_presentation=True).get_latest_version()
        except IndexError:
            return None

    def __unicode__(self):
        return unicode(self.user)
    
    class Admin:
        search_fields = ['user__username']
    
    class Meta:
        verbose_name = _('meta user')
        verbose_name_plural = _('meta users')
        
def user_unicode(self):
    if self.first_name != '':
        return self.first_name + ' ' + self.last_name
    elif self.email != '':
        return self.email
    else:
        return self.username
User.__unicode__ = user_unicode

def user_get_absolute_url(self):
    return '/users/%d/' % self.id
User.get_absolute_url = user_get_absolute_url

def group_absolute_url(self):
    url = 'http://community.%s/' % self.meta.domain
    # this fiddling with the URL is to support running the dev version under eldmyra.se
    if get_current_request().META['HTTP_HOST'].endswith('eldmyra.net') and url.endswith('eldmyra.se/'):
        url = url[:-3]+'net/'
    return url
Group.get_absolute_url = group_absolute_url

def group_external_absolute_url(self):
    return 'http://%s/' % self.meta.domain
Group.get_external_absolute_url = group_external_absolute_url

class MetaGroup(models.Model):
    group = models.OneToOneField(Group, primary_key=True, related_name='meta', verbose_name=_('Group'))
    created_by = models.ForeignKey(User, blank=True, null=True, related_name='created_groups', verbose_name=_('Created by'))
    children = models.ManyToManyField('self', related_name='parents', symmetrical=False, blank=True)
    friend_group = models.BooleanField(default=False, blank=True, verbose_name=_('Friend group'))
    logo = models.ImageField(upload_to='group-logos', blank=True, verbose_name=_('Logo'))
    deleted = models.BooleanField(default=False, verbose_name=_('Deleted'))
    deleted_by = models.ForeignKey(User, blank=True, null=True, default=None, related_name='deleted_groups', verbose_name=_('Deleted by'))
    deletion_time = models.DateTimeField(blank=True, null=True, verbose_name=_('Deletion time'))
    domain = models.CharField(blank=True, null=True, max_length=200, unique=True, verbose_name=_('Domain name'))
    external_theme = models.CharField(blank=True, max_length=100, verbose_name=_('External theme'))
    internal_theme = models.CharField(blank=True, max_length=100, verbose_name=_('Internal theme'))
    
    def presentation(self):
        try:
            from curia.documents.models import Document
            return Document.objects.get(owner_group=self.group, is_presentation=True).get_latest_version()
        except IndexError:
            return None

    def __unicode__(self):
        return smart_unicode(self.group)

    class Admin:
        search_fields = ['group__name']
        
    class Meta:
        verbose_name = _('meta group')
        verbose_name_plural = _('meta groups')
        
class Invite(models.Model):
    REPLY_CHOICES = (
        ('Y', _('Yes')),
        ('N', _('No')),
        ('-', _('No reply')),
    )
    
    group = models.ForeignKey(Group, verbose_name=_('Group'))
    user = models.ForeignKey(User, related_name='group_answers', verbose_name=_('User'))
    inviter = models.ForeignKey(User, related_name='group_invited_users', verbose_name=_('Inviter'))
    choice = models.CharField(max_length=1, choices=REPLY_CHOICES, default='-', verbose_name=_('Choice'))
    message = models.TextField(blank=True)
    
    def __unicode__(self):
        if self.choice == '-':
            return u'%s hasn\'t replied to %s' % (self.user, self.group)
        else:
            return u'%s replied "%s" to %s' % (self.user, self.choice, self.group)

    class Admin:
        search_fields = ['user__email']

    class Meta:
        verbose_name = _('invite')

def resize_group_picture(sender, instance, **kwargs):
    from PIL import Image
    # This function is called twice for file uploads, because the object is saved twice: once without the file on 
    # disk and one with. We ignore the first save by checking if the filename has been set yet
    if instance.logo:
        try:
            pic = Image.open(instance.logo.path())
            pic.thumbnail(settings.LOGO_SIZE, Image.ANTIALIAS)
            pic.save(instance.logo.path)
        except KeyError:
            pass

signals.post_save.connect(resize_group_picture, sender=MetaGroup)
