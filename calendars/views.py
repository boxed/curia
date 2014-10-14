from datetime import datetime, timedelta
from django.shortcuts import *
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.simplejson import dumps 
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext as _
from django.utils.encoding import smart_unicode
import django.forms
from curia import *
from curia.shortcuts import *
from curia.calendars.models import Event, Reply
from curia.notifications import *
from curia.notifications.models import Watcher, Notification
from curia.labels import handle_labels, mark_labels_as_deleted
from curia.authentication.models import UserPermission
from curia.labels import handle_labels, mark_labels_as_deleted, get_labels

def view_month_for_user(request, user_id, year, month):
    user = get_object_or_404_and_check_access(request, User, pk=user_id, command='view')
    start_span = datetime(int(year), int(month), 1)
    end_span = first_of_next_month(start_span)
    events = Event.objects.filter(owner_user=user, start_time__lt=end_span, end_time__gt=start_span, repeat='', deleted=False)
    #TODO: repeat_events = Event.objects.filter(owner_user=user, start_time__lt=end_span, end_repeat__gt=start_span, repeat__not='')
    from django.core import serializers
    dump = dumps({'year':year, 'month':month, 'events':u'<replace>'}, ensure_ascii=False)
    result = dump.replace(u'"<replace>"', smart_unicode(serializers.serialize("json", events, ensure_ascii=False)))

    return HttpResponse(result, content_type="text/json; charset=UTF-8")

def view_month_for_group(request, year, month, group_id=None):
    if group_id != None:
        group = get_object_or_404_and_check_access(request, Group, pk=group_id, command='view')
    else:
        group = get_current_community()
    start_span = datetime(int(year), int(month), 1)
    end_span = first_of_next_month(start_span)
    events = Event.objects.filter(owner_group=group, start_time__lt=end_span, end_time__gt=start_span, repeat='', deleted=False)
    #TODO: repeat_events = Event.objects.filter(owner_group=group, start_time__lt=end_span, end_repeat__gt=start_span, repeat__not='')
    from django.core import serializers

    return HttpResponse(dumps({'year':year, 'month':month, 'events':'<replace>'}, ensure_ascii=False).replace('"<replace>"', serializers.serialize("json", events)), content_type="text/json; charset=UTF-8")

def delete_event(request, event_id):
    from curia import delete_object
    event = Event.objects.get(pk=event_id)
    check_access(request.user, event, command='change event')
    delete_object(event)
    
    #Change any children
    if not event.event_parent:
        event_children = event.event_children.all()
        for child in event_children:
            try:
                child.description = _("This event has been deleted by its creator.")
                child.save()
            except:
                pass            
  
    #If this is a copy, change answer to no.
    if event.event_parent:
        parent = event.event_parent
        reply = get_object_or_404(Reply, event=parent, user=request.user)
        reply.choice = 'N'
        reply.save()
    
    mark_labels_as_deleted(event, request.user)
  
    from django.core import serializers
    return HttpResponse(dumps(event_id, ensure_ascii=False), content_type="text/json; charset=UTF-8")

# this function is needed because there is some problem with import ordering that intermittently produces errors for this file    
def get_event_form():
    from curia.forms import SplitDateTimeWidget2
    import django.forms
    class EventForm(django.forms.Form):
        title = django.forms.CharField(label=_('Event'), help_text=_('The title will be visible in the calendar'))
        labels = django.forms.CharField(label=_('Labels'), required=False, help_text=_('Help your friends find this item'))
        description = django.forms.CharField(widget = django.forms.Textarea, required=False, label=_('Description'))
        start_time = django.forms.SplitDateTimeField(label=_('Start time'), widget=SplitDateTimeWidget2())
    return EventForm
    
## Not currently used  
# def validate_invites(form,event=None):
#     usernames = map(lambda x: x.strip(), form.data['invite_users'].split(','))
#     groupnames = map(lambda x: x.strip(), form.data['invite_groups'].split(','))
#     
#     users = []
#     errors = []
#     for username in usernames:
#         if username != '':
#             try:
#                 user = User.objects.get(username=username)
#                 try:
#                     Reply.objects.get(user=user,event=event)
#                 except:
#                     users.append(user)
#             except User.DoesNotExist:
#                 errors.append('no username "%s"' % username)
#     
#     if len(errors) != 0:        
#         form.errors['invite_users'] = errors
# 
#     groups = []
#     errors = []
#     for groupname in groupnames:
#         if groupname == 'everyone':
#             errors.append('no group "%s"' % groupname)
#         elif groupname != '':
#             try:
#                 group = Group.objects.get(name=groupname)
#                 groups.append(group)
#             except Group.DoesNotExist:
#                 errors.append('no group "%s"' % groupname)
#     
#     if len(errors) != 0:        
#         form.errors['invite_groups'] = errors
#     
#     return (users, groups)
    
def handle_invites(inviter, event, users):
    for user in users:
        try:
            Reply.objects.get(inviter=inviter, event=event, user=user)
        except Reply.DoesNotExist:
            Reply.objects.create(inviter=inviter, event=event, user=user)

def edit_event(request, event_id):
    event = Event.objects.get(pk=event_id)
    check_access(request.user, event, command='change event')
    if not event.event_parent:
        if request.POST:
            form = get_event_form()(request.POST)
            #users, groups = validate_invites(form,event)

            if not form.errors:
                event.title=form.data['title']
                event.description=form.data['description'] 
                event.start_time=form.data['start_time_0']+' '+form.data['start_time_1']
                event.end_time=form.data['start_time_0']+' '+form.data['start_time_1']
                event.save()
        
                #Change all children
                event_children = event.event_children.all()
                for child in event_children:
                    try:
                        django.forms.models.save_instance(form, child)
                    except:
                        pass            

                #handle_invites(request.user, event, users, groups)
                handle_labels(request, event)
                
                if event.owner_group != None:
                    return HttpResponseRedirect('/calendars/groups/%s/agenda/' % (event.owner_group.id,))
                else:
                    return HttpResponseRedirect('/calendars/users/%s/agenda/' % (event.owner_user.id,))
        else:
            form = get_event_form()(initial={'start_time':event.start_time, 'end_time':event.end_time, 'title':event.title, 'description':event.description, 'all_day':event.all_day, 'labels': ', '.join([unicode(label) for label in get_labels(event)])})
    else:
        form = get_event_form()(initial={'start_time':event.start_time, 'end_time':event.end_time, 'title':event.title, 'description':event.description, 'all_day':event.all_day, 'labels': ', '.join([unicode(label) for label in get_labels(edit)])})

    return render_to_response(request, 'calendars/edit.html', {'event': event, 'form': form})
    
def view_event(request, event_id):
    event = get_object_or_404_and_check_access(request, Event, pk=event_id, command='view')
    test = event.owner_user

    #If this is a copy, get the original answers.
    if event.event_parent:
        original = event.event_parent
    else:
        original = event
    
    yes_replies = Reply.objects.filter(event=original, choice='Y').order_by('choice')
    no_replies = Reply.objects.filter(event=original, choice='N').order_by('choice')
    unsure_replies = Reply.objects.filter(event=original, choice='?').order_by('choice')
    not_answered = Reply.objects.filter(event=original, choice='-').order_by('choice')
    
    try:
        reply = get_object_or_404(Reply, event=original, user=request.user)
        class ReplyForm(django.forms.Form):
            choice = django.forms.ChoiceField(choices=Reply.REPLY_CHOICES, label=_('Choice'))
            comment = django.forms.CharField(required=False, label=_('Comment'))

        if request.POST:
            form = ReplyForm(request.POST)
            if form.is_valid():
                reply.choice = form.cleaned_data['choice']
                reply.comment = form.cleaned_data['comment']
                reply.save()
                
                #If the answer is yes, copy it to the users calender
                if reply.choice == 'Y' or reply.choice == '?':
                    try:
                        event_copy = Event.objects.get(event_parent=original, owner_user = request.user, deleted=False)
                    except:
                        if not event.owner_user == request.user:
                            event_copy = Event.objects.create(title=event.title, description=event.description, start_time=event.start_time, end_time=event.end_time, owner_user=request.user, all_day=event.all_day, event_parent=event)    
                            content_type = get_content_type(event)
                            watcher = Watcher(user=request.user, object_id=event_copy.id, content_type=content_type, owner_user=event.owner_user, inverse=False)
                            watcher.save()
                        
                return HttpResponseRedirect(request.user.get_absolute_url())
        else:
            form = ReplyForm(initial={})
            form.fields['choice'].initial = reply.choice
            form.fields['comment'].initial = reply.comment
    except:
        form = 'None'

    return render_to_response(request, 'calendars/view_event.html', {'event': event, 'yes_replies':yes_replies, 'no_replies':no_replies, 'unsure_replies':unsure_replies, 'not_answered':not_answered, 'owner':get_owner(event), 'form':form})

## Not currently used  
# def add_event_to_user(request, user_id):
#     user = get_object_or_404_and_check_access(request, User, pk=user_id, command='add')
#     check_access(request.user, obj=user, command='add event')
#     
#     if request.POST:
#         form = get_event_form()(request.POST)
#         #users, groups = validate_invites(form)
#         
#         if form.data['start_time'] > form.data['end_time']:
#             form.errors['end_time'] = (_('The end of the event has to be after the beginning.'),)
#         
#         if form.is_valid():
#             event = Event.objects.create(title=form.cleaned_data['title'], description=form.cleaned_data['description'], start_time=form.cleaned_data['start_time'], end_time=form.cleaned_data['end_time'], owner_user=user, all_day=form.cleaned_data['all_day'])
#             content_type = get_content_type(event)
#             
#             #handle_invites(request.user, event, users, groups)
#             handle_labels(request, event)
#             if event.owner_group != None:
#                 return HttpResponseRedirect('/calendars/groups/%s/aganda/' % (event.owner_group.id,))
#             else:
#                 return HttpResponseRedirect('/calendars/users/%s/agenda/' % (event.owner_user.id,))
#     else:
#         form = get_event_form()(initial={})
#         if 'date' in request.GET:
#             form.fields['start_time'].initial = request.GET['date']+' 12:00'
#             #form.fields['end_time'].initial = form.fields['start_time'].initial
#         else:
#             form.fields['start_time'].initial = datetime.now()
#             #form.fields['end_time'].initial = datetime.now()
#     
#     return render_to_response(request, 'calendars/add.html', {'form': form})

def add_event_to_group(request, group_id=None):
    if group_id != None:
        group = get_object_or_404_and_check_access(request, Group, pk=group_id, command='add')
    else:
        group = request.community
    check_access(request.user, obj=group, command='add event')

    if request.POST:
        form = get_event_form()(request.POST)
        #users, groups = validate_invites(form)

        #if form.data['start_time'] > form.data['end_time']:
        #    form.errors['end_time'] = (_('The end of the event has to be after the beginning.'),)

        if form.is_valid():
            event = Event.objects.create(
                title=form.cleaned_data['title'], 
                description=form.cleaned_data['description'], 
                start_time=form.cleaned_data['start_time'], 
                end_time=form.cleaned_data['start_time'],#form.cleaned_data['end_time'], 
                owner_group=group,
                owner_user=request.user, 
                all_day=False)#all_day=form.cleaned_data['all_day'])
            
            handle_invites(request.user, event, group.user_set.all())
            handle_labels(request, event)
            
            if event.owner_group != None:
                return HttpResponseRedirect('/calendars/groups/%s/agenda/' % (event.owner_group.id,))
            else:
                return HttpResponseRedirect('/calendars/users/%s/agenda/' % (event.owner_user.id,))
    else:
        form = get_event_form()(initial={})
        if 'date' in request.GET:
            form.fields['start_time'].initial = request.GET['date']+' 12:00'
            #form.fields['end_time'].initial = form.fields['start_time'].initial
        else:
            print form.fields
            form.fields['start_time'].initial = datetime.now()
            #form.fields['end_time'].initial = datetime.now()
            
    return render_to_response(request, 'calendars/add.html', {'form': form})
 
#def reply_to_event(request, event_id):
#    event = get_object_or_404_and_check_access(request, Event, pk=event_id, command='view')
#    reply = get_object_or_404(Reply, event=event, user=request.user)
#     
#    class ReplyForm(django.forms.Form):
#        choice = django.forms.ChoiceField(choices=Reply.REPLY_CHOICES, label=_('Choice'))
#        comment = django.forms.CharField(required=False, label=_('Comment'))
# 
#    if request.POST:
#        form = ReplyForm(request.POST)
#        
#        if form.is_valid():
#            reply.choice = form.cleaned_data['choice']
#            reply.comment = form.cleaned_data['comment']
#            reply.save()
#              
#            #If the answer is yes, copy it to the users calender
#            #if reply.choice == 'Y' or reply.choice == '?':
#                    #watcher = Watcher(user=request.user, object_id=event_copy.id, content_type=content_type, owner_user=event.owner_user, negate=False)
#                    #watcher.save()
# 
#            return HttpResponseRedirect('calendars/')
#    else:
#        form = ReplyForm(initial={'choice':'-'})
#         
#    return render_to_response(request, 'calendars/reply_to_event.html', {'event':event, 'form':form})    

def reply_to_event(request, event_id):
    event = get_object_or_404_and_check_access(request, Event, pk=event_id, command='view')
    try:
        reply = Reply.objects.get(event=event, user=request.user)
    except Reply.DoesNotExist:
        reply = Reply(event=event, user=request.user, choice='-', inviter=request.user)
    
    import django.forms
    class ReplyForm(django.forms.Form):
        choice = django.forms.ChoiceField(choices=(('Y', 'Yes'), ('N', 'No'), ('?', '?'),), label=_('Choice'), help_text=_('Will you participate in this event?'), widget = django.forms.RadioSelect)
        comment = django.forms.CharField(required=False, label=_('Comment'), help_text=_('Leave a comment with your reply'))
    
    if request.POST:
        form = ReplyForm(request.POST)

        if form.is_valid():            
            reply.choice = form.cleaned_data['choice']
            reply.comment = form.cleaned_data['comment']
            reply.save()
            from curia.times import set_time_on
            set_time_on(event)
            return HttpResponseRedirect('/calendars/agenda/')
    else:
        form = ReplyForm(initial={'choice':reply.choice, 'comment':reply.comment})     
            
    return render_to_response(request, 'calendars/reply.html', {'form': form})

def reply(request, event_id, new_reply):
    event = get_object_or_404_and_check_access(request, Event, pk=event_id, command='view')
    try:
        reply = Reply.objects.get(event=event, user=request.user)
    except Reply.DoesNotExist:
        reply = Reply(event=event, user=request.user, choice='-', inviter=request.user)

    if new_reply == 'U':
        new_reply = '?'
    if new_reply == 'Y' or new_reply == 'N' or new_reply == '?':
        reply.choice = new_reply
        reply.save()
    
    from curia.times import set_time_on
    set_time_on(event)
    
    return HttpResponseRedirect('/calendars/agenda/')    

## Not currently used      
# def view_user(request, user_id):
#     user = get_object_or_404_and_check_access(request, User, pk=user_id, command='view')
#     return render_to_response(request, 'calendars/view.html', {'object':user, 'object_type':'user', 'owner':user})
        
def view_group(request, group_id=None):
    if group_id != None:
        group = get_object_or_404_and_check_access(request, Group, pk=group_id, command='view')
    else:
        group = get_current_community()
    return render_to_response(request, 'calendars/view.html', {'object':group, 'object_type':'group', 'owner':group})

## Not currently used    
# def view_agenda_of_user(request, user_id):
#     user = get_object_or_404_and_check_access(request, User, pk=user_id, command='view')
#     start_span = start_of_day(datetime.now())
#     end_span = start_span+timedelta(weeks=4)
#     events = Event.objects.filter(owner_user=user, start_time__lt=end_span, end_time__gt=start_span, repeat='', deleted=False)
#     return render_to_response(request, 'calendars/view_agenda.html', {'object':user, 'object_type':'user', 'owner':user, 'events':events})
#     
def view_agenda_of_group(request, group_id=None):
    replies = Reply.objects.filter(user=request.user)
    if group_id != None:
        group = get_object_or_404_and_check_access(request, Group, pk=group_id, command='view')
    else:
        group = get_current_community()
    start_span = start_of_day(datetime.now())-timedelta(hours=3)
    end_span = start_span+timedelta(weeks=20)
    events = Event.objects.filter(owner_group=group, start_time__lt=end_span, end_time__gt=start_span, repeat='', deleted=False)
   
    return render_to_response(request, 'calendars/view_agenda.html', {'object':group, 'object_type':'group', 'owner':group, 'events':events, 'user':request.user})
    
def show_replies_of_event(request, event_id):
    event = Event.objects.get(owner_group=request.community, deleted=False, pk=event_id)
    event.Y = Reply.objects.filter(event=event, choice='Y')
    event.N = Reply.objects.filter(event=event, choice='N')
    event.unknown = Reply.objects.filter(event=event, choice='?')
    event.noreply = Reply.objects.filter(event=event, choice='-')

    return render_to_response(request, 'calendars/show_replies.html', {'event':event})

