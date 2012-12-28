from django.contrib.auth.views import login_required
from django.contrib.auth.models import User, Group
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import *
from curia.notifications.models import *
from curia.shortcuts import *
from datetime import datetime
from curia import *
from curia.authentication import *
import exceptions
from django.utils.translation import ugettext as _
from django.core.paginator import Paginator

# types and helpers
class NotificationException(exceptions.Exception):
    def __init__(self, str):
        self.str = str
        
    def __unicode__(self):
        return self.str

@login_required
def view_watchers(request):
    watchers = Watcher.objects.filter(user=request.user)
    return render_to_response(request, 'notifications/list.html', {'watchers':watchers})

@login_required
def delete_notification(request, notification_id):
    obj = get_object_or_404(Notification, pk=notification_id)
    check_perm(request.user, obj.user, 'delete')
    obj.delete()
    return HttpResponseRedirect('/notifications/')

@login_required
def delete_watcher(request, watcher_id):
    obj = get_object_or_404(Watcher, pk=watcher_id)
    check_perm(request.user, obj.user, 'delete')
    obj.delete()
    return HttpResponseRedirect('/notifications/watchers/')    

@login_required
def view_bookmarks(request):
    bookmarks = Bookmark.objects.filter(user=request.user)
    return render_to_response(request, 'notifications/view_bookmarks.html', {'bookmarks':bookmarks})
    
@login_required
def watch(request, object_id=None, cls=None, owner_user_id=None, owner_group_id=None, content_type=None, bookmark=False):
    owner_user = None
    if owner_user_id:
        owner_user = User.objects.get(pk=owner_user_id)
        
    owner_group = None
    if owner_group_id:
        owner_group = Group.objects.get(pk=owner_group_id)
    
    if isinstance(content_type, str):
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get(name=content_type) 
    if cls:
        content_type = get_content_type(cls)
    
    if owner_group == None and owner_user == None:
        if content_type != None:
            obj = content_type.get_object_for_this_type(pk=object_id)
            if isinstance(obj, User):
                owner_user = obj
                object_id = None
                content_type = None
            elif isinstance(obj, Group):
                owner_group = obj
                object_id = None
                content_type = None
            else:
                owner_user = obj.owner_user
                owner_group = obj.owner_group
        else:
            raise NotificationException('owner_group or owner_user must be set')

    if owner_group != None:
        owner_user = None
    
    # if a negation exists, just delete it and don't add a specific watcher
    f = get_objects_from(Watcher, user=request.user, object_id=object_id, content_type=content_type, owner_group=owner_group, owner_user=owner_user, inverse=True)
    if len(f) == 0:
        watcher = Watcher(user=request.user, object_id=object_id, content_type=content_type, owner_group=owner_group, owner_user=owner_user, inverse=False)
        watcher.save()
    else:
        for i in f:
            i.delete()
    
    return HttpResponseRedirect(request.META['HTTP_REFERER'])

@login_required
def ignore(request, object_id=None, cls=None, owner_user_id=None, owner_group_id=None, content_type=None):
    if isinstance(content_type, str) or isinstance(content_type, unicode):
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get(name=content_type) 
    if cls:
        content_type = get_content_type(cls)

    if owner_group_id == None and owner_user_id == None:
        if content_type != None:
            obj = content_type.get_object_for_this_type(pk=object_id)
            if isinstance(obj, User):
                owner_user = obj
                owner_group = None
                object_id = None
                content_type = None
            elif isinstance(obj, Group):
                owner_user = None
                owner_group = obj
                object_id = None
                content_type = None
            else:
                owner_user = obj.owner_user
                owner_group = obj.owner_group
        else:
            raise NotificationException('owner_group or owner_user must be set')
    else:
        owner_user = get_object_or_none(User, owner_user_id)
        owner_group = get_object_or_none(Group, owner_group_id)

    if owner_group != None:
        owner_user = None
            
    f = get_objects_from(Watcher, object_id=object_id, owner_user=owner_user, owner_group=owner_group, content_type=content_type, user=request.user)
    
    if len(f) == 0:
        # no watcher found, add an ignore
        watcher = Watcher(object_id=object_id, owner_user=owner_user, owner_group=owner_group, content_type=content_type, user=request.user, inverse=True)
        watcher.save()
        i = watcher
    else:
        # watcher found, delete it
        for i in f:
            i.delete()
        
    return HttpResponseRedirect(request.META['HTTP_REFERER'])

@login_required
def add_bookmark(request):
    title = request.REQUEST['title']
    url = request.REQUEST['url']
    Bookmark.objects.create(user=request.user, title=title, url=url)
    
    return HttpResponseRedirect(url)

@login_required
def delete_bookmark(request, bookmark_id=None):
    if bookmark_id == None:
        bookmark = Bookmark.objects.get(url=request.REQUEST['url'], user=request.user)
        url = bookmark.url
        bookmark.delete()
    else:
        bookmark = Bookmark.objects.get(pk=bookmark_id, user=request.user)
        url = bookmark.url
        bookmark.delete()
        
    return HttpResponseRedirect(url)

@login_required
def view_new_objects(request, content_type_id):
    from django.contrib.contenttypes.models import ContentType
    content_type = ContentType.objects.get(pk=content_type_id)
    # TODO: add pagination instead of this hack. Note that pagination leads to some redesigns of the handling of delete_new_objects_of_type()
    class NewObject:
        def __getitem__(self, i):
            return self.object_list[i]

        def __len__(self):
            return len(self.object_list)
    new_objects = NewObject()
    new_objects.object_list = content_type.model_class().objects.in_bulk([x.object_id for x in SubscriptionResult.objects.filter(content_type=content_type, user=request.user, originator_group=request.community)]).values()
    return render_to_response(request, 'notifications/view_new_objects.html', 
        {
        'content_type': unicode(content_type.model_class()._meta),
        'content_type_name': content_type.model_class()._meta.verbose_name_plural.lower(),
        'new_objects':new_objects,
        'content_id':content_type_id
        })
        
@login_required
def delete_new_objects_of_type(request, content_type_id):
    content_type = ContentType.objects.get(pk=content_type_id)
    SubscriptionResult.objects.filter(content_type=content_type, user=request.user).delete()
    return HttpResponseRedirect('/')