from datetime import datetime
from curia import *
from curia.notifications import remove_notification
from django.utils.translation import ugettext as _

def get_last_changed(obj):
    from curia.times.models import Time
    
    try:
        time = get_objects_from(Time, user=None, content_type=get_content_type(obj).id, object_id=obj.id)[0]
    except IndexError:
        try:
            time = Time(user=None, content_type=get_content_type(obj), object_id=obj.id, last_viewed=obj.last_changed_time)
        except AttributeError:
            try:
                time = Time(user=None, content_type=get_content_type(obj), object_id=obj.id, last_viewed=obj.creation_time)
            except AttributeError:
                time = Time(user=None, content_type=get_content_type(obj), object_id=obj.id)
        
    return time

def get_time_from(obj, user):
    from curia.times.models import Time
    from curia.messages.models import Message
    
    if obj.__class__ == Time:
        return obj
        
    object_id = obj.id
    
    if obj.__class__ == Message:
        object_id = obj.sender.id
    
    try:
        time = get_objects_from(Time, user=user, content_type=get_content_type(obj).id, object_id=object_id)[0]
    except IndexError:
        time = Time(user=user, content_type=get_content_type(obj), object_id=object_id)
    
    return time

def set_time_on(obj, user = None, new_time = None):
    time = get_time_from(obj, user)
    if user == None:
        user = get_current_user()
    if new_time == None:
        new_time = datetime.now()
    time.last_viewed = new_time
    
    from django.db import IntegrityError
    try:
        time.save()
    except IntegrityError:
        pass
        
    remove_notification(user, obj)