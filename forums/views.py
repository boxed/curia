from datetime import datetime
from django.contrib.auth.models import Group
from django.db.models import F
from django.utils.translation import ugettext as _
from django.http import HttpResponse, HttpResponseRedirect
from django.core.paginator import Paginator
from django.shortcuts import *
from django.conf import settings
from curia import *
from curia.forums.models import Thread, Message
from curia.times import set_time_on, get_time_from
from curia.shortcuts import *
from curia.authentication import check_access
from curia.notifications.models import *
from curia.labels import handle_labels, search_objects_from, get_labels
from curia.labels.models import SuggestedLabel

def get_add_form():
    import django.forms
    class AddForm(django.forms.Form):
        name = django.forms.CharField(max_length=50, label=_('Title'))
        labels = django.forms.CharField(required=False, label=_('Labels'))
        first_message = django.forms.CharField(widget = django.forms.Textarea, label='')
    return AddForm

def view_forum(request, group_id=None, suggested_label_title=None, page=None):
    if group_id:
        group = get_object_or_404_and_check_access(request, Group, pk=group_id, command='view')
    else:
        group=request.community
    check_access(request.user, group, 'view')
    page_size = get_integer(request, 'page_size', default=12)
    search = get_string(request, 'search', default='')
  
    suggested_labels = get_objects_from(SuggestedLabel, deleted=False, group=group_id, content_type=get_content_type(Thread))

    import django.forms
    class SearchForm(django.forms.Form):
        search = django.forms.CharField(max_length=2048, label=_('Search'), required=False)
       
    if request.POST:
        form = SearchForm(request.POST)

        if form.is_valid():
            if 'create_thread' in request.REQUEST and request.REQUEST['create_thread'] == _('Create thread'):
                return HttpResponseRedirect('/forums/add/?group_id=%s&labels=%s' % (group.id,  get_string(request, 'fastsearch', default='')) )
            return HttpResponseRedirect('/forums/%s/?search=%s&fastsearch=%s' % (group_id, search, get_string(request, 'fastsearch', default='')))
    else:
        form = SearchForm(initial={'search':search})
    
    full_search = search+','+get_string(request, 'fastsearch', default='')
    if full_search == ',': 
        full_search = ''
    threads = search_objects_from(full_search, Thread, owner_group=group)
    
    paginator = Paginator(threads.order_by('-last_changed_time'), page_size)

    number_of_pages = paginator.num_pages
    got_page_size = False

    if number_of_pages != 0:
        if not page:
            page = 1
        page = int(page)
        # TODO: implement getting page ranges
        #end_page = int(request.GET['end_page'])
        end_page = page
        threads = paginator.page(page)
    else:
        end_page = 0
        page = 0
        threads = []

    next_page = page+1
    has_next_page = paginator.page(page).has_next()
    
    on_all = True
    for suggested_label in suggested_labels:
        if suggested_label.title == get_string(request, 'fastsearch', default=''):
            on_all = False

    return render_to_response(request, 'forums/view_forum.html', 
        {
            'base_url':'/forums/'+str(group.id)+'/', 
            'is_paginated':True, 
            'form':form, 
            'threads':threads, 
            'suggested_labels':suggested_labels, 
            'group':group, 
            'number_of_pages':number_of_pages, 
            'page':page, 
            'end_page':end_page, 
            'has_next_page':has_next_page, 
            'has_previous_page':paginator.page(page).has_previous(), 
            'next_page':next_page, 
            'previous_page':page - 1, 
            'page_size':page_size, 
            'search': search,
            'fastsearch': get_string(request, 'fastsearch', default=''),
            'on_all':on_all,
            'paginator':paginator,
            'add_form':get_add_form()(initial={})
        })

def view_thread(request, thread_id, page=None):
    thread = get_object_or_404_and_check_access(request, Thread, pk=thread_id, command='view')
    page_size = get_integer(request, 'page_size', default=12)
    orphans=10
    
    try:    
        set_time_on(thread, request.user, datetime_from_string(request.GET['set_time']))
        set_time = False
    except KeyError:
        set_time = True
        
    last_viewed = get_time_from(thread, request.user).last_viewed
    try:
        time = datetime_from_string(request.GET['time'])
    except KeyError:
        time = last_viewed
        
    message_query = Message.objects.filter(parent_thread__pk=thread_id)
    show_deleted = get_boolean(request, 'show_deleted')

    if not show_deleted:
        message_query = message_query.filter(deleted=show_deleted)
        
    threaded = get_boolean(request, 'threaded', settings.THREADED_FORUMS)
    
    if threaded:
        message_order_by = 'cache_hierarchy'
    else:
        message_order_by = 'creation_time'
        
    paginator = Paginator(message_query.order_by(message_order_by), page_size, orphans=orphans)

    number_of_pages = paginator.num_pages
    got_page_size = False
    
    if number_of_pages != 0:
        if not page:
            page = number_of_pages
        page = int(page)
 
        # TODO: implement getting page ranges
        #end_page = int(request.GET['end_page'])
        end_page = page

        messages = paginator.page(page)
    else:
        end_page = 0
        page = 0
        messages = []
        
    next_page = page+1
    has_next_page = paginator.page(page).has_next()

    messages = list(messages.object_list)
    if threaded:
        try:
          # get "first" (i.e. the upper most on the page) new message: the message with lowest cache_hierarchy, of the messages that have a timestamp set after "time"
          if time is None:
              time = datetime.fromordinal(1)
          first_message = Message.objects.filter(parent_thread=thread, creation_time__gt=time).order_by(message_order_by)[0]

          # if we didn't get an explicit request for a specific page and the current page does not include the "first" (i.e. the upper most on the page) unread message
          if not got_page_size:
              while first_message not in messages and page > 1:
                  # extend one page
                  end_page = page
                  page -= 1
                  tmp = messages
                  messages = paginator.page(page).object_list
                  messages.extend(tmp)

          # set firstnew on the first unread message in the page
          for message in messages:
              if time is None or message.creation_time >= last_viewed:
                  message.firstnew = True
                  break
                            
        except IndexError:
          # for correct scrolling: set firstnew flag on the last message if there are no unread messages
          if len(messages) != 0:
              messages[-1].firstnew = True
    else: # not threaded
        has_unread = False
        # set firstnew on the first unread message in the page
        for message in messages:
          if time is None or message.creation_time >= last_viewed:
              message.firstnew = True
              has_unread = True
              break
              
        # for correct scrolling: set firstnew flag on the last message if there are no unread messages
        if not has_unread:
            messages[-1].firstnew = True
   
    # If this is in a forum, get list of suggested_labels.
    suggested_label = None
    parents = None    
    forum = False
    if thread.owner_group is None:
        forum = True
        parents = []
        try:
            suggested_label = request.GET['suggested_label']
            tp = SuggestedLabel.objects.get(title=suggested_label)
        except (KeyError, SuggestedLabel.DoesNotExist):
            tp = None
        suggested_label = tp
        suggested_labels = get_objects_from(SuggestedLabel, deleted=False, parent=tp)
        
        if tp == None:
            pass
        else:
            if tp.parent:
                has_parent = True
                while has_parent:
                    parents.append(tp.parent)
                    m = tp.parent
                    if not m.parent:
                        has_parent = False
                    tp = tp.parent
                parents.reverse()
                
    #Add message
    import django.forms
    class EditForm(django.forms.Form):
        body = django.forms.CharField(widget = django.forms.Textarea, label=_('Message'))

    parent_message = None   
    if request.REQUEST.has_key('parent_message_id') and request.REQUEST['parent_message_id'] != '':
        parent_message = Message.objects.get(pk=request.REQUEST['parent_message_id'])
            
    if request.method == 'POST':
        form = EditForm(request.POST)
        check_access(request.user, command='add message', obj=thread) # NOTE: same command in message.html and view_thread.html

        if form.is_valid():
            import re
            replacer = re.compile('&nbsp;')
            body = form.cleaned_data['body']
            body = replacer.sub(' ', body)
            if body != '':
                Message.objects.create(parent_thread=thread, parent_message=parent_message, owner=request.user, body=body)
                thread.last_changed_by = request.user
                thread.last_changed_time = datetime.now()
                thread.save()

                Thread.objects.filter(pk=thread.id).update(count=F('number_of_replies')+1)

                set_time_on(thread, user=None)

            try:
                Watcher.objects.get(object_id=thread.id, user=request.user, content_type=ContentType.objects.get(name="thread"))
            except Watcher.DoesNotExist:
                Watcher.objects.create(user=request.user, object_id=thread.id, owner_user=request.user, owner_group=request.community, content_type=ContentType.objects.get(name="thread"))
      
            return HttpResponseRedirect(thread.get_absolute_url()+'?time='+str(time)+'#firstnew')
            
    else:
        form = EditForm(initial={})
            
    return render_to_response(
        request, 
        'forums/view_thread.html', 
        {
            'watch_object':thread,
            'thread':thread, 
            'messages':messages, 
            'number_of_pages':number_of_pages, 
            'page':page,
            'end_page':end_page,
            'has_next_page': has_next_page,
            'has_previous_page': paginator.page(page).has_previous(),
            'next_page':next_page,
            'previous_page':page - 1,
            'page_size':page_size,
            'show_deleted':show_deleted,
            'time':time,
            'set_time':set_time,
            'owner':get_owner(thread),
            'suggested_label':suggested_label,
            'parents':parents,
            'forum': forum,
            'form': form,
            'is_paginated':True,
            'base_url':thread.get_absolute_url(),
            'threaded':threaded,
            'number_of_replies':thread.number_of_replies,
            'current_user':request.user,
            'paginator':paginator
            
        })

def delete_message(request, message_id):
    message = get_object_or_404(Message, pk=message_id)
    
    if message.owner != request.user:
        check_access(request.user, obj=message.parent_thread, command='administrate thread')

    new_messages = Message.objects.filter(parent_thread=message.parent_thread, creation_time__gt=message.creation_time, deleted=False).count()

    thread = message.parent_thread
    if new_messages != 0:
        check_access(request.user, command='administrate thread', obj=thread)
        
    delete_object(message)
    Thread.objects.filter(pk=thread.id).update(count=F('number_of_replies')+1)
    if thread.number_of_replies == 0:
        delete_object(thread)
    
    # disconnect replies
    for reply in Message.objects.filter(parent_message=message):
        reply.parent_message = None
        reply.save()
        
    from django.utils.simplejson import dumps 
    return HttpResponse(dumps([message.id], ensure_ascii=False), content_type='text/json; charset=UTF-8')

def edit_message(request, message_id):
    message = get_object_or_404(Message, pk=message_id)
    try:
        time = datetime_from_string(request.GET['time'])
    except KeyError:
        time = get_time_from(message.parent_thread, request.user).last_viewed

    import django.forms   
    class EditForm(django.forms.Form):
        message = django.forms.CharField(widget = django.forms.Textarea, label=_('Message'))

    if message.owner == request.user:
        if request.method == 'POST':
            form = EditForm(request.POST)

            if form.is_valid():
                import re
                replacer = re.compile('&nbsp;')
                body = form.cleaned_data['message']
                body = replacer.sub(' ', body)
                message.body = body
                message.save()

                return HttpResponseRedirect(message.parent_thread.get_absolute_url()+'?time='+str(time)+'#firstnew')
        else:
            form = EditForm(initial={'message':message.body})         
    else:
        form = EditForm(initial={})              
    return render_to_response(request, 'forums/edit_message.html', {'form':form})

def add_thread(request, suggested_label=None):
    if request.POST:
        form = get_add_form()(request.POST)

        if form.is_valid():
            group_id = get_integer(request, 'group_id')
            user_id = get_integer(request, 'user_id')
            if group_id:
                owner_group = Group.objects.get(pk=group_id)
                check_access(request.user, obj=owner_group, command='add thread')
                thread = Thread.objects.create(owner_group=owner_group, owner_user=request.user, name=form.cleaned_data['name'], last_changed_by=request.user, last_changed_time=datetime.now())
                Watcher.objects.create(user=request.user, object_id=thread.id, owner_user=request.user, owner_group=owner_group, content_type=ContentType.objects.get(name="thread"))
            else:
                owner_group = request.community
                check_access(request.user, obj=owner_group, command='add thread')
                thread = Thread.objects.create(owner_group=owner_group, owner_user=request.user, name=form.cleaned_data['name'], last_changed_by=request.user, last_changed_time=datetime.now())
                Watcher.objects.create(user=request.user, object_id=thread.id, owner_user=request.user, owner_group=owner_group, content_type=ContentType.objects.get(name="thread"))
                         
            if form.cleaned_data['first_message'] != '':
                import re
                replacer = re.compile('&nbsp;')
                body = form.cleaned_data['first_message']
                body = replacer.sub(' ', body)
                Message.objects.create(body=body, parent_thread=thread, owner=request.user)
        
            #Handle the labels
            handle_labels(request,thread)

            return HttpResponseRedirect(thread.get_absolute_url())
    
    labels = get_string(request, 'labels', default='')
   
    form = get_add_form()(initial={'title':'', 'contents':'', 'labels':labels})

    return render_to_response(request, 'forums/add.html', {'form': form})
    
def edit_thread(request, thread_id):
    thread = get_object_or_404_and_check_access(request, Thread, pk=thread_id, command='edit')
    
    import django.forms
    class EditForm(django.forms.Form):
        name = django.forms.CharField(max_length=1024, label=_('Name'), help_text=_('The title will be visible in the thread list'))
        labels = django.forms.CharField(required=False, label=_('Labels'), help_text=_('Help your friends find this item'))
        
    if request.POST:
        form = EditForm(request.POST)
        
        #Handle the labels
        handle_labels(request,thread)

        if form.is_valid():
            thread.name = form.cleaned_data['name']
            thread.save()
            return HttpResponseRedirect(thread.get_absolute_url())
    else:
        form = EditForm({'name': thread.name, 'labels': ', '.join([unicode(label) for label in get_labels(thread)])})
        
    return render_to_response(request, 'forums/edit.html', {'form':form, 'thread':thread})
    
def delete_thread(request, thread_id):
    thread = get_object_or_404_and_check_access(request, Thread, pk=thread_id, command='delete')
    delete_object(thread)

    from django.utils.simplejson import dumps 
    return HttpResponse(dumps(thread.id, ensure_ascii=False), content_type="text/json; charset=UTF-8")