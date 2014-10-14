from curia.files.models import File
from curia.shortcuts import *
from django.http import HttpResponse, HttpResponseRedirect

from datetime import datetime
from django.core.paginator import Paginator, InvalidPage
from django.contrib.auth.models import User, Group
from django.shortcuts import get_object_or_404
from django.utils.simplejson import dumps
from django.utils.translation import ugettext as _
from sets import Set
from curia.labels import get_labels
from curia.labels.models import Label
from curia.labels import handle_labels, mark_labels_as_deleted, search_objects_from, get_labels, get_objects_with_label
from curia import *
from curia.forms import *

from curia.authentication.models import UserPermission
import django.forms

def add_file(request):
    labels = ''
    class AddForm(django.forms.Form):
        title = django.forms.CharField(label=_('Title'), required=True, help_text=_('The title will be visible in the file list'))
        labels = django.forms.CharField(required=False, label=_('Labels'), help_text=_('Help your friends find this item'))
        description = django.forms.CharField(required=False, widget = django.forms.Textarea, label=_('Description'))
        file = django.forms.FileField(required=False, label=_('File'))
    
    if request.POST:
        new_data = request.POST.copy()
        new_data.update(request.FILES)
        form = AddForm(new_data)

        if form.is_valid():
            if 'file' in new_data:  
                f = File.objects.create(owner_user=request.user, owner_group=request.community, title=form.cleaned_data['title'], description=form.cleaned_data['description'])
                save_file_for_object(obj=f, fieldname='file', data=new_data)
                
                handle_labels(request,f)

                return HttpResponseRedirect('/files/')
    else:
        try:
            labels = request.REQUEST['labels']
        except:
            labels = ''
        form = AddForm(initial={'labels':labels})
    
    return render_to_response(request, 'files/add.html', {'form':form, 'labels':labels})
 
def delete_file(request, file_id):
    file = get_object_or_404_and_check_access(request, File, pk=file_id, command='delete')
    
    from curia import delete_object
    delete_object(file)
    
    return HttpResponse(dumps(file_id, ensure_ascii=False), content_type="text/json; charset=UTF-8")

def edit_file(request, file_id):
    file = get_object_or_404_and_check_access(request, File, pk=file_id, command='edit')

    class EditForm(django.forms.Form):
        title = django.forms.CharField(label=_('Title'), required=True, help_text=_('The title will be visible in the file list'))
        labels = django.forms.CharField(required=False, label=_('Labels'), help_text=_('Help your friends find this item'))
        description = django.forms.CharField(widget = django.forms.Textarea, label=_('Description'))
        
    if request.POST:
        form = EditForm(request.POST)

        if form.is_valid():
            file.title = form.cleaned_data['title']
            file.description = form.cleaned_data['description']
            file.save()
            
            #Handle the labels
            handle_labels(request,file)
            
            if file.owner_group:
                return HttpResponseRedirect('/files/groups/%s/' % (file.owner_group.id,))
            else:
                return HttpResponseRedirect('/files/users/%s/' % (file.owner_user.id,))

    else:
        form = EditForm({'description': file.description, 'title': file.title, 'labels': ', '.join([unicode(label) for label in get_labels(file)])})
                
    return render_to_response(request, 'files/edit.html', {'form':form, 'file': file})

## Not currently used
# def view_files_of_user(request, user_id):
#     user = get_object_or_404_and_check_access(request, User, pk=user_id, command='view')
#     objects = get_objects_from(File, deleted=False, owner_user=user, owner_group=None)
# 
#     return render_to_response(request, 'files/file_list.html', {'owner':user, 'objects':objects, 'type':'users'})
    
def view_files_of_group(request, group_id=None, suggested_label_title=None, page=None):
    from curia.labels.models import SuggestedLabel
    if group_id != None:
        group = get_object_or_404_and_check_access(request, Group, pk=group_id, command='view')
    else:
        group = get_current_community()
        
    page_size = get_integer(request, 'page_size', default=10)
    search = get_string(request, 'search', default='')
  
    suggested_labels = get_objects_from(SuggestedLabel, deleted=False, group=group_id, content_type=get_content_type(File))
    
    class SearchForm(django.forms.Form):
        search = django.forms.CharField(max_length=2048, label=_('Search'), required=False)
       
    if request.POST:
        form = SearchForm(request.POST)

        if form.is_valid():
            if 'upload_file' in request.REQUEST and request.REQUEST['upload_file'] == _('Upload file'):
                return HttpResponseRedirect('/files/add/?group_id=%s&fastsearch=%s' % (group.id, get_string(request, 'fastsearch', default='')))
            return HttpResponseRedirect('/files/groups/%s/?search=%s&fastsearch=%s' % (group_id, search, get_string(request, 'fastsearch', default='')))
 
    else:
        form = SearchForm(initial={'search':search})
    
    full_search = search+','+get_string(request, 'fastsearch', default='')
    files = search_objects_from(full_search, File, owner_group=group)
    
    paginator = Paginator(files.order_by('-creation_time'), page_size)

    number_of_pages = paginator.num_pages
    got_page_size = False

    if number_of_pages != 0:
        if not page:
            page = 1
        page = int(page)
        # TODO: implement getting page ranges
        #end_page = int(request.GET['end_page'])
        end_page = page
        files = paginator.page(page)
    else:
        end_page = 0
        page = 0
        files = []

    next_page = page+1
    has_next_page = paginator.page(page).has_next()
    
    on_all = True
    for suggested_label in suggested_labels:
        if suggested_label.title == get_string(request, 'fastsearch', default=''):
            on_all = False

    return render_to_response(request, 'files/view_files.html', 
        {
            'owner':group,
            'user':request.user,
            'files':files,
            'type':'groups',
            'base_url':'/files/groups/'+str(group.id)+'/', 
            'is_paginated':True, 
            'form':form, 
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
            'fastsearch': get_string(request, 'fastsearch', default=''),
            'search': search,
            'on_all': on_all,
            'paginator':paginator
        })