from curia import *
from django.utils.translation import ugettext as _

def notify(sender, instance, **kwargs):
    from curia.notifications.models import Watcher, Notification, SubscriptionResult

    try:
        if instance.deleted:
            # remove any previous notification that is still left
            content_type = get_content_type(instance)
            Notification.objects.filter(object_id=instance.pk, content_type=content_type).delete()  
            Watcher.objects.filter(object_id=instance.pk, content_type=content_type).delete()  
            SubscriptionResult.objects.filter(object_id=instance.pk, content_type=content_type).delete()
            return
    except AttributeError:
        pass
    
    # notify all users that have registered for this specific object 
    for registration in Watcher.objects.filter(content_type=get_content_type(instance), object_id=instance.pk, inverse=False):
        try:
            if registration.user != instance.last_changed_by:
                notify_user(registration.user, instance)
        except:
            pass

    # notify all users that have registered for this content type and this user/group
    if hasattr(instance, 'owner_user') and hasattr(instance, 'owner_group'):
        for registration in get_objects_from(Watcher, owner_user=instance.owner_user, owner_group=instance.owner_group, content_type=get_content_type(instance), object_id=None, inverse=False):
            try:
                if registration.user != instance.last_changed_by:
                    notify_user(registration.user, instance)
            except:
                pass
            
        if instance.owner_group == None:
            # notify all users that have registered for this user
            for registration in get_objects_from(Watcher, owner_user=instance.owner_user, owner_group=None, content_type=None, object_id=None, inverse=False):
                try:
                    if registration.user != instance.last_changed_by:
                        notify_user(registration.user, instance)
                except:
                    pass
                    
        else:
            # notify all users that have registered for this user
            for registration in get_objects_from(Watcher, owner_user=None, owner_group=instance.owner_group, content_type=None, object_id=None, inverse=False):
                try:
                    if registration.user != instance.last_changed_by:    
                        notify_user(registration.user, instance)
                except:
                    pass
    
def notify_user(user, instance, **kwargs):
    from curia.notifications.models import Notification, Watcher
    content_type = get_content_type(instance)
    
    from curia.authentication import has_perm    
    if has_perm(user, instance, 'view'):
        # handle negations on this specific object (this is redundant if this function was called for a specific notification on this object)
        if Watcher.objects.filter(user=user, content_type=content_type, object_id=instance.pk, inverse=True).count() != 0:
            return
    
        # handle negations on this content type for this user/group
        if Watcher.objects.filter(user=user, content_type=content_type, object_id__isnull=True, inverse=True).count() != 0:
            return
        
        owner_user = None
        owner_group = None
        if hasattr(instance, 'owner'):
            owner_user = instance.owner
        if hasattr(instance, 'owner_user'):
            owner_user = instance.owner_user
        if hasattr(instance, 'owner_group'):
            owner_group = instance.owner_group
            
        try:
            new_notification = Notification(user=user, object_id=instance.pk, content_type=content_type, title=unicode(instance), url=instance.get_absolute_url(), originator_user=get_current_user(), originator_group=get_current_community())
            new_notification.save()
            
            if user.notification_style == 'E': # notify on every event
                            send_notification_mail(user, new_notification)
        except:
            pass
        
def remove_notification(user, instance):
    from curia.notifications.models import Notification, SubscriptionResult
    from curia.messages.models import Message
    if isinstance(instance, Message):
        Notification.objects.filter(user=user, object_id=instance.sender.id, content_type=get_content_type(instance)).delete()
        Notification.objects.filter(user=user, object_id=instance.receiver.id, content_type=get_content_type(instance)).delete()
    else:
        Notification.objects.filter(user=user, object_id=instance.pk, content_type=get_content_type(instance)).delete()
        
    SubscriptionResult.objects.filter(user=user, object_id=instance.pk, content_type=get_content_type(instance)).delete()

def on_added_label(label):
    from curia.notifications.models import IgnoreLabel
    for ignore_label in IgnoreLabel.objects.filter(label=label.name):
        # remove from users list of new objects
        from curia.notifications.models import SubscriptionResult
        SubscriptionResult.objects.filter(content_type=label.content_type, object_id=label.object_id, user=ignore_label.user).delete()
    
def update_subscription(sender, instance, **kwargs):
    from curia.notifications.models import SubscriptionResult
    if kwargs['created']:
        from curia.labels.models import Label
        if isinstance(instance, Label):
            on_added_label(instance)
        else:

            # add this object to all the community members' list of new objects
            for user in get_community_of(instance).user_set.all():
                if user != get_current_user():
                    SubscriptionResult.objects.create(user=user, content_type=get_content_type(instance), object_id=instance.pk, originator_user=get_current_user(), originator_group=get_current_community())
    else:
        try:
            if instance.deleted:
                SubscriptionResult.objects.filter(content_type=get_content_type(instance), object_id=instance.pk).delete()
        except AttributeError:
            pass

def enable_notifications(cls):
    from django.db.models import signals
    signals.post_save.connect(notify, sender=cls)
    signals.post_save.connect(update_subscription, sender=cls)
    
def user_is_watching(user, owner_user=None, owner_group=None, owner=None, content_type=None, object_id=None, obj=None):
    from django.contrib.auth.models import User
    
    if owner != None:
        if isinstance(owner, User):
            owner_user = owner
        else:
            owner_group = owner
    
    if obj != None:
        if callable(obj):
            obj = obj()
        object_id = obj.id
        content_type = get_content_type(obj)
        owner_user = obj.owner_user
        owner_group = obj.owner_group
    
    if isinstance(content_type, str):
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get(name=content_type)

    if owner_user == None and owner_group == None:
        import exceptions
        raise exceptions.Exception('owner_user or owner_group must be set')

    if owner_group != None:
        owner_user = None
    
    from django.contrib.auth.models import User, Group
    from curia.notifications.models import Watcher
    
    watchers = get_objects_from(Watcher, owner_user=owner_user, owner_group=owner_group, content_type=content_type, object_id=object_id, user=user)
    
    # if there is a watcher directly on the target        
    if len(watchers) != 0:
        return watchers[0].inverse == False
    else:
        # if the target is a user or group, return False
        if content_type == None:
            return False

        # if the target is a content_type: check the owner
        if object_id == None:
            return user_is_watching(user, owner_user, owner_group)
        else:
            # target is an object: check the content_type, then the owner if the content_type is not watched
            watchers = get_objects_from(Watcher, owner_user=owner_user, owner_group=owner_group, content_type=content_type, object_id=None, user=user)
            if len(watchers):
                return watchers[0].inverse == False
            else:
                return user_is_watching(user, owner_user, owner_group)
                
def add_patterns(urlpatterns, cls, prefix=''):
    from django.conf.urls import patterns
    urlpatterns += patterns('curia.notifications.views',
        (r'^'+prefix+r'(?P<object_id>\d+)/watch/$', 'watch', {'cls': cls}),
        (r'^'+prefix+r'(?P<object_id>\d+)/ignore/$', 'ignore', {'cls': cls}),
    )

def get_users_to_email():
    # mail only users that have notifications and that are active, and that have not opted out
    from datetime import datetime, timedelta
    one_week_ago = datetime.now()-timedelta(days=7)

    from django.db import connection
    cursor = connection.cursor()
    cursor.execute("SELECT user_id FROM (SELECT DISTINCT user_id, last_login FROM notifications_notification INNER JOIN auth_user ON user_id = auth_user.id) AS foo WHERE last_login < %s", [one_week_ago])

    from django.contrib.auth.models import User
    users = User.objects.in_bulk([x[0] for x in cursor.fetchall()]).values()
    for user in users:
        if not user.is_active:
            del user
        elif user.meta.last_notification_email_time != None: # we've mailed once at least
            date_diff = datetime.now() - user.meta.last_notification_email_time

            # mail when that user has not been notified for a month or a year respectively
            if date_diff < timedelta(days=30):
                # we've mailed once, but one month has not passed yet, don't mail this user
                del user
            elif date_diff > timedelta(days=30) and datetime.now() - user.meta.last_notification_email_time < timedelta(weeks=52):
                # we've mailed the month mail and a year hasn't passed yet
                del user
        else: 
            date_diff = datetime.now() - user.last_login
            
            # don't mail users that haven't been away for more than a week
            if date_diff < timedelta(days=7):
                del user

    return users

def get_subscription_entries(user, community):
    from django.db import connection
    cursor = connection.cursor()
    class SubscriptionEntry:
        def __init__(self, count, content_type_id):
            self.content_type_id = content_type_id
            from django.contrib.contenttypes.models import ContentType
            self.content_type = ContentType.objects.get(pk=self.content_type_id)
            self.count = count

        def __unicode__(self):
            from django.template.defaultfilters import pluralize
            if self.count == 1:
                return _('%(count)s new %(item)s') % {'count': self.count, 'item':self.content_type.model_class()._meta.verbose_name.lower()}
            else:
                return _('%(count)s new %(items)s') % {'count': self.count, 'items':self.content_type.model_class()._meta.verbose_name_plural.lower()}

    subscription_entries = []
    cursor.execute('SELECT COUNT(*), content_type_id FROM notifications_subscriptionresult WHERE user_id = %s AND originator_group_id = %s GROUP BY content_type_id' % (user.id, community.id))
    for entry in cursor.fetchall():
        subscription_entries.append(SubscriptionEntry(entry[0], entry[1]))
    return subscription_entries
