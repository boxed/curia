from django.db import models
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext_lazy as _
from curia.notifications import enable_notifications
from django.dispatch import dispatcher
from django.db.models import signals
from curia import get_content_type
from django.utils.encoding import smart_unicode

class Message(models.Model):
    sender = models.ForeignKey(User, related_name='private_messages_sent_set')
    receiver = models.ForeignKey(User, related_name='private_message_received_set')
    message = models.TextField(verbose_name=_('Message'))
    creation_time = models.DateTimeField(auto_now_add=True, verbose_name=_('Creation time'))
    
    def get_absolute_url(self):
        return '/messages/%s/?user=%s' % (self.receiver.id, self.sender.id)
        
    def __unicode__(self):
        return u'%s to %s' % (self.sender, self.receiver)
    
    class Admin:
        pass
        
    class Meta:
        ordering = ('creation_time',)
        
def get_users_with_messages_related_to(user_id = None, user = None):
    # get a list of unique users where sender or reciever is user_id
    from sets import Set
    if user_id is None:
        user_id = user.id
        
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute("SELECT DISTINCT sender_id FROM messages_message WHERE receiver_id = %s", [user_id])
    user_ids = Set([x[0] for x in cursor.fetchall()])
    cursor.execute("SELECT DISTINCT receiver_id FROM messages_message WHERE sender_id = %s", [user_id])
    user_ids = list(user_ids | Set([x[0] for x in cursor.fetchall()]))
    
    users = User.objects.in_bulk(user_ids).values()
    users.sort(lambda x, y: cmp(x.username.lower(), y.username.lower()))

    return users 

def notify_message(sender, instance, **kwargs):
    from curia.notifications.models import Notification
    try:
        Notification.objects.get(user=instance.receiver, object_id=instance.sender.id, content_type=get_content_type(instance))
    except Notification.DoesNotExist:
        new_notification = Notification(user=instance.receiver, object_id=instance.sender.id, content_type=get_content_type(instance), title=u'%s: %s' % (smart_unicode(instance.sender), smart_unicode(instance.message[:17])), url=instance.get_absolute_url())
        new_notification.save()

signals.post_save.connect(notify_message, sender=Message)
