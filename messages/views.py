from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User, Group
from django.http import HttpResponse, HttpResponseRedirect
from curia.messages.models import *
from curia.shortcuts import *
from django.shortcuts import get_object_or_404

from django.core.paginator import Paginator, InvalidPage
from django.utils.translation import ugettext as _

def add_thread(request):
    receiver_id = get_integer(request, 'receiver_id')
    owner_id = get_integer(request, 'owner_id')
    owner = request.user

    if owner_id:
        owner = get_object_or_404(User, pk=owner_id)
    sender = request.user
    
    if receiver_id:
        receiver = get_object_or_404(User, pk=receiver_id)
        class MessageForm(django.forms.Form):
            message = django.forms.CharField(widget = django.forms.Textarea, label=_('Message'), required=True)
    else:
        class MessageForm(django.forms.Form):
            receiver = django.forms.CharField(label=_('Receiver'), required=True)
            message = django.forms.CharField(widget = django.forms.Textarea, label=_('Message'), required=True)
            
    if request.POST:
        form = MessageForm(request.POST)
        
        if form.is_valid():
            if not receiver_id:
                try:
                    receiver = User.objects.get(username=form.cleaned_data['receiver']) 
                    if receiver == request.user:    
                        form.errors['receiver'] = (_('You cannot send a message to yourself.'),)
                        receiver = None
                    
                except User.DoesNotExist:
                    form.errors['receiver'] = (_('No user with that name exists'),)
                    receiver = None
            
            Message.objects.create(sender=sender, receiver=receiver, message=form.cleaned_data['message'])
    else:
        form = MessageForm(initial={})
        
    if request.user == owner:
        try:
            return HttpResponseRedirect('/messages/%s/?user=%s' % (request.user.id, receiver.id))
        except:
            return render_to_response(request, 'messages/add.html', {'form':form})
  
    return HttpResponseRedirect('/messages/%s/?user=%s' % (receiver.id, request.user.id))

def view_messages(request, user_id):
    user = get_object_or_404_and_check_access(request, User, pk=user_id, command='view')
    from curia.messages.models import Message, get_users_with_messages_related_to
    objects = {}
    user2 = None
    
    if request.user == user:
        objects['users'] = get_users_with_messages_related_to(user_id)
        if 'user' in request.GET:
            user2 = User.objects.get(pk=request.GET['user'])
            objects['user'] = user2
            
    else:
        user2 = user 
        objects['user'] = user2
        
    try:
        page_size = int(request.GET['page_size'])
    except:
        page_size = 7 # get from user settings
    
    from django.db.models import Q
    message_query = Message.objects.filter(Q(receiver=request.user) & Q(sender=user2) | Q(sender=request.user) & Q(receiver=user2))

    paginator = Paginator(message_query.order_by('creation_time'), page_size)

    number_of_pages = paginator.num_pages
    got_page_size = False

    if number_of_pages != 0:
        try:
            page = int(request.GET['page'])
            got_page_size = True
        except:
            page = number_of_pages

        end_page = page

        messages = paginator.page(page)
    else:
        end_page = 0
        page = 0
        messages = []
        
        
    # if we didn't get an explicit request for a specific page and the current page is too small, and we're not on the first page
    if got_page_size == False and len(messages) <= page_size/2 and page is not 1 and number_of_pages != 0:
        # extend one page
        end_page = page
        page -= 1
        tmp = messages
        messages = list(paginator.page(page))
        messages.extend(tmp)
        

    objects['messages'] = messages
    objects['page'] = page
    objects['end_page'] = end_page
    objects['number_of_pages'] = number_of_pages
    objects['has_next_page'] = paginator.page(page).has_next()
    objects['has_previous_page'] = paginator.page(page).has_previous()
    objects['next_page'] = page + 1
    objects['previous_page'] = page - 1
    objects['page_size'] = page_size

    return render_to_response(request, 'messages/message_list.html', {'objects':objects, 'owner': user, 'receiver':user2})