from django.db import models
from django.contrib.auth.models import User,Group
from curia.notifications import enable_notifications
from django.db.models import signals
from django.utils.translation import ugettext_lazy as _

class Thread(models.Model):
    name = models.CharField(max_length=767, null=True, name=_('Name'))
    owner_user = models.ForeignKey(User, blank=True, null=True, verbose_name=_('Owner user'), name=_('owner user'))
    owner_group = models.ForeignKey(Group, blank=True, null=True, verbose_name=_('Owner group'), name=_('owner group'))
    creation_time = models.DateTimeField(auto_now_add=True, name=_('Creation time'))
    last_changed_time = models.DateTimeField(auto_now_add=True, name=_('Last changed time'))
    deleted = models.BooleanField(default=False, name=_('Deleted'))
    deleted_by = models.ForeignKey(User, blank=True, null=True, default=None, related_name="deleted_forums", name=_('Deleted by'))
    deletion_time = models.DateTimeField(blank=True, null=True, name=_('Deletion time'))
    last_changed_by = models.ForeignKey(User, related_name='messages_that_are_latest_in_threads', name=_('Last changed by'))
    number_of_replies = models.IntegerField(default=0, name=_('Number of replies'))

    def has_default_permission(self, user, command):
        from curia.authentication import PermissionResponse
        if command == 'add message':
            return PermissionResponse(True, 'users can reply to threads by default')
    
    def save(self, force_insert=False, using=None):
        if self.owner_user is None and self.owner_group is None:
            raise ValueError('A thread must be owned by a user or a group.')
    
        models.Model.save(self, force_insert, using=using)
    
    def get_absolute_url(self):
        return '/forums/threads/%s/' % self.id
    
    def __unicode__(self):
        return self.name
    
    class Admin:
        search_fields = ['name']
    
    class Meta:
        verbose_name = _('thread')
        verbose_name_plural = _('threads')

enable_notifications(Thread)

class Message(models.Model):
    body = models.TextField(name=_('Body'))
    parent_thread = models.ForeignKey(Thread, related_name='child_message', name=_('Thread'))
    parent_message = models.ForeignKey('self', null=True, blank=True, related_name='child_message', name=_('Parent message'))
    cache_hierarchy = models.CharField(max_length=767, null=True, blank=True, editable=False, db_index=True)
    owner = models.ForeignKey(User, related_name='thread_messages', name=_('Owner'))
    creation_time = models.DateTimeField(auto_now_add=True, name=_('Creation time'))
    deleted = models.BooleanField(default=False, name=_('Deleted'))
    deleted_by = models.ForeignKey(User, blank=True, null=True, default=None, related_name="deleted_messages", name=_('Deleted by'))
    owner_group = property(lambda self:self.parent_thread.owner_group, lambda self:None)   
                
    def get_indent(self):
        return len(self.cache_hierarchy)/8-1
    
    def __unicode__(self):
        return self.body[:20]
        
    class Admin:
        search_fields = ['owner__username']
        
    class Meta:
        verbose_name = _('message')
        verbose_name_plural = _('messages')

def encode(pk):
    from binascii import b2a_uu
    from struct import pack
    return b2a_uu(pack('!L', pk))[0:-1]

def set_cache_hierarchy(sender, instance, **kwargs):
    if not hasattr(instance, 'avoid_infinite_loop') and instance.cache_heirarchy is None:
        instance.avoid_infinite_loop = True
        if instance.parent_message:
            instance.cache_hierarchy = Message.objects.get(id=instance.parent_message.id).cache_hierarchy+encode(instance.id)
        else:
            instance.cache_hierarchy = encode(instance.id)
        
        models.Model.save(instance, False)
        del instance.avoid_infinite_loop
        
def notify_message(sender, instance, **kwargs):
    from curia.notifications import notify
    if not instance.deleted:
        notify(sender, instance.parent_thread)

signals.post_save.connect(set_cache_hierarchy, sender=Message)
signals.post_save.connect(notify_message, sender=Message)
