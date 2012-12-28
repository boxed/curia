
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import *
from django.db.models import Q
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext as _
from django.utils.encoding import smart_unicode
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from curia import *
from curia.shortcuts import *
from curia.labels import get_objects_with_label
from curia.labels.models import Label
from curia.notifications.models import Notification, Bookmark, SubscriptionResult
from curia.calendars.models import Reply
from curia.authentication import has_perm, get_public_user
from curia.authentication.models import Invite
from curia.base.models import News
from curia.forums.models import Thread
from curia.documents.models import Document, Version
from curia.authentication.models import UserPermission

def index(request):
    if request.external:
        if request.mode == 'admin':
            from curia.homepage.views import admin_index
            return admin_index(request)
            
        return external(request)
            
    if request.user.is_anonymous():
        return HttpResponseRedirect('/login/')

    return portal(request)
    
def external(request):
    if request.community == None:
        return render_to_response(request, '404_community.html')

    # get first menu item and display it
    from curia.homepage.models import MenuItem
    try:
        home = MenuItem.objects.filter(parent__isnull=True, group=request.community)[0]
        from curia.documents.views import version_response, get_latest
        v = get_latest(home.object_id)
        check_access(get_public_user(), obj=v.document, command='view')
        if v == None:
            raise Http404
        return version_response(request, v)
    except IndexError:
        return render_to_response(request, 'no_external_page_error.html')
    
def contents(request):
    return render_to_response(request, 'contents.html')

def search(request):
    tags_result = None
    users_result = None
    groups_result = None
    search_words = ''
    search_words = request.REQUEST['search']
    q = None
    q2 = None
    for word in map(lambda x: x.strip(), search_words.split(',')):
        if q == None:
            q = Q(name__iexact=word)
        else:
            q |= Q(name__iexact=word)

        if q2 == None:
            q2 = Q(username__iexact=word)
        else:
            q2 |= Q(username__iexact=word)

    users_result = User.objects.filter(q2)
    groups_result = Group.objects.filter(q)
    tags_result = Label.objects.filter(q)
    if len(tags_result) > 1:
        tags_result = [tags_result[0]]
    
    if len(users_result) == 1 and len(groups_result) == 0 and len(tags_result) == 0:
        has_access = has_perm(request.user, users_result[0], 'view')
        if has_access:    
            return HttpResponseRedirect(users_result[0].get_absolute_url())
    
    if len(users_result) == 0 and len(groups_result) == 1 and len(tags_result) == 0:
        has_access = has_perm(request.user, groups_result[0], 'view')
        if has_access:
            return HttpResponseRedirect(groups_result[0].get_absolute_url())

    return render_to_response(request, 'search.html', {'search_words': search_words, 'tags_result': tags_result, 'users_result':users_result, 'groups_result':groups_result})

#def navigation(request):
#    return navigation(request, template='navigation.html')

def navigation_ajax(request, template='navigation_core.html'):
    try:
        if 'current_url' in request.REQUEST:
            current_url = request.REQUEST['current_url']
        else:
            current_url = None

        notifications = []
        event_invites = []
        group_invites = []
        bookmarks = []
        subscription_entries = []
        communities = []
        unread_other_communities = False

        if request.user.is_authenticated():
            notifications = Notification.objects.filter(user=request.user, originator_group=request.community)
            event_invites = Reply.objects.filter(choice='-', user=request.user) 
            group_invites = Invite.objects.filter(choice='-', user=request.user)
            bookmarks = Bookmark.objects.filter(user=request.user)
            communities = request.user.groups.exclude(name='everyone')
        
            for community in communities:
                community.number_of_notifications = Notification.objects.filter(user=request.user, originator_group=community).count()
                community.number_of_new_objects = SubscriptionResult.objects.filter(user=request.user, originator_group=community).count()
            
                if (community.number_of_new_objects != 0 or community.number_of_notifications != 0) and community != request.community:
                    unread_other_communities = True
        
            from curia.notifications import get_subscription_entries
            subscription_entries = get_subscription_entries(request.user, request.community)
        
        from django.template import loader, Context
        from django.utils.simplejson import dumps
        from django.template import RequestContext

        c = RequestContext(request)
        c.update({
            'current_url_is_bookmarked':current_url in [x.url for x in bookmarks],
            'notifications':notifications,
            'event_invites':event_invites, 
            'group_invites':group_invites, 
            'bookmarks':bookmarks,
            'subscription_entries':subscription_entries,    
            'communities':communities,
            'unread_other_communities':unread_other_communities,
            })
    
        button = ''
        if len(communities) > 1:
            button = loader.get_template('community_selector_button.html').render(c)
        
        return HttpResponse(dumps([
            loader.get_template('community_selector.html').render(c), 
            button, 
            loader.get_template(template).render(c),
            ], ensure_ascii=False), mimetype="text/json; charset=UTF-8")
        # return render_to_response(request, template, {
        #     'current_url_is_bookmarked':current_url in [x.url for x in bookmarks],
        #     'notifications':notifications,
        #     'event_invites':event_invites, 
        #     'group_invites':group_invites, 
        #     'bookmarks':bookmarks,
        #     'subscription_entries':subscription_entries,    
        # })
    except IOError:
        pass

def notification_check(request):
    from django.contrib.auth import authenticate
    try:
        username = User.objects.get(email=request.REQUEST['username']).username
        user = authenticate(username=username, password=request.REQUEST['password'])
        count = Notification.objects.filter(user=user).count()+SubscriptionResult.objects.filter(user=user).count()
        return HttpResponse(str(count))
    except:
        import sys
        return HttpResponse('failed to login (%s, %s)' % (sys.exc_type, sys.exc_value))

def stylesheet(request, template, mimetype='text/css'):
    user_agent = request.META['HTTP_USER_AGENT'].lower()
    if 'ie' in user_agent:
        browser = 'ie'
    elif 'webkit' in user_agent:
        browser = 'webkit'
    elif 'mozilla' in user_agent:
        browser = 'mozilla'
    elif 'opera' in user_agent:
        browser = 'opera'
    else:
        browser = 'unknown'
    
    from django.template import loader
    from django.http import HttpResponse, Http404
    from django.template import RequestContext
        
    return HttpResponse(loader.render_to_string(template, context_instance=RequestContext(request), dictionary={'browser':browser, 'user_agent':user_agent}), mimetype=mimetype)
        
def portal(request):
    if request.community == None:
        return render_to_response(request, '404_community.html')

    check_access(request.user, request.community, command='view')
    
    from curia.calendars.models import Event
    from curia.images.models import Image
    import datetime
    today = datetime.date.today()

    events = Event.objects.filter(end_time__gt=today, start_time__lt=today+datetime.timedelta(days=4), owner_group=request.community, deleted=False).order_by('start_time')
    bugs = ''
    if request.user.is_superuser:
        from curia.bugs.models import Bug
        c = Bug.objects.filter(deleted=False).count()
        if c != 0:
            bugs = 'There are %s bugs reported' % c
      
    # select u from User u, MetaUser mu, UserInGroup uig where uig.group_id = VARIABEL and u.id = uig.user_id and mu.user_id = u.id and mu.image is not null order by last_login limit 3

    try:    
        presentation = Document.objects.get(owner_user__isnull=True, owner_group=request.community, is_presentation=True)
    except Document.DoesNotExist:
        # this is a brand new community, so we need to set some initial data

        # create presentation
        presentation = Document.objects.create(owner_user=None, owner_group=request.community, is_presentation=True)
        title = 'Presentation'
        new_version = Version(document=presentation, title=title, contents=_('Welcome!'), owner=request.user)
        new_version.save()
    
    presentation = presentation.get_latest_version().contents
    return render_to_response(request, 'portal.html', 
        {
            'community':request.community,
            'events': events, 
            'news':News.objects.filter(deleted=False).order_by('-creation_time')[:3], 
            'bugs':bugs,
            'random_images':Image.objects.filter(owner_group=request.community, deleted=False).order_by('?')[:6],
            'latest_logged_in':request.community.user_set.order_by('-last_login')[:4],
            'presentation':presentation
        })

def administrate(request):
    group = request.community
    administrators = {}
    check_access(request.user, group, command='administrate group')

    permissions = UserPermission.objects.filter(command__contains='administrate', object_id=group.id)
    for permission in permissions:
        if not permission.user in administrators: 
            administrators[permission.user] = {'user':permission.user}
        administrators[permission.user][permission.command.replace(' ', '_')] = True
        
    administration_content_types = [
        ('thread', _('Forum')),
        ('file', _('Files')),
        ('image_set', _('Images')),
        ('event' , _('Calendar')),
    ]

    if request.POST:
        def handle_admin(user, id_key=None):
            if id_key == None:
                id_key = user.id
            for content_type in administration_content_types:
                key = '%s_%s' % (id_key, content_type[0])
                if key in request.POST:
                    try: 
                        permission = UserPermission.objects.get(user=user, command='administrate '+content_type[0].replace('_', ' '), content_type=get_content_type(group), object_id=group.id)
                    except UserPermission.DoesNotExist:
                        UserPermission.objects.create(user=user, command='administrate '+content_type[0].replace('_', ' '), content_type=get_content_type(group), object_id=group.id)
                else:
                    try: 
                        UserPermission.objects.get(user=user, command='administrate '+content_type[0].replace('_', ' '), content_type=get_content_type(group), object_id=group.id).delete()
                    except UserPermission.DoesNotExist:
                        pass
        
        for admin in administrators:
            handle_admin(admin)
        
        if 'new_user_id' in request.POST:
            new_admin = User.objects.get(pk=request.POST['new_user_id'])
            handle_admin(new_admin, 'new')
        
        return HttpResponseRedirect('/administration/')
    else:
        pass
        
    non_admins = []
    for member in request.community.user_set.all():
        if member not in administrators:
            non_admins.append(member)
    
    return render_to_response(request, 'administrate.html', {
        'administrators':administrators, 
        'non_admins': non_admins, 
        'permissions':permissions, 
        'content_types':administration_content_types,
        })
    
def delete_administration_access(request, user_id):
    group = request.community
    user = User.objects.get(pk=user_id)
    check_access(request.user, group, command='administrate group')
        
    UserPermission.objects.filter(user=user, command__contains='administrate', object_id=group.id).delete()

    return HttpResponseRedirect('/administration/')