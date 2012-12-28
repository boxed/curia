import re
from datetime import datetime
from django.contrib.auth.views import login_required
from django.http import HttpResponse, HttpResponseRedirect

from django.utils.simplejson import dumps 
from django.contrib.auth.models import User,Group
from django.utils.encoding import smart_unicode
from curia.documents.models import Document, Version
from curia.shortcuts import *
from curia import *
from django.utils.translation import ugettext as _
from sets import Set
from curia.labels import get_labels
from curia.labels.models import Label
from curia.labels import handle_labels, mark_labels_as_deleted

# helper
def get_latest(document_id):
    try: return Version.objects.filter(document=document_id).order_by('-id')[0]
    except Version.DoesNotExist: return None;

def validate_wiki_links(owner_user, owner_group, form, contents_name = 'contents'):
    from django.utils.encoding import smart_unicode
    contents = smart_unicode(form.data[contents_name])
    links = list(re.finditer(r'(\[(.*?)\])', contents))
    
    errors = []
    
    link_targets = {}
    
    # examples of use:
    # [images/groups/1/sets/3]
    
    for link in links:
        title = link.groups()[1]
        if ';' in title:
            group_name, title = title.split(u';')
            group = get_objects_from(Group, name=group_name)
            if len(group) == 1:
                owner_group = group[0]
            else:
                user = get_objects_from(User, username=group_name)
                if len(user) == 1:
                    owner_user = user[0]
                else:
                    errors.append(_('%s is not a valid group or user name') % group_name)
                    continue
                    
        documents = get_objects_from(Document, owner_user=owner_user, owner_group=owner_group, title=title, deleted=False)
        if len(documents) != 1:
            errors.append(_('Could not find document %s') % link.groups()[1])
        else:
            link_targets[link.groups()[1]] = documents[0]
            
    if len(errors) != 0:
        form.errors[contents_name] = errors
    else:
        # replace from the end as to not change the string in a way that interferes with the following replace operation
        links.reverse()
        
        for link in links:
            target = link_targets[link.groups()[1]]
            contents = contents.replace(link.groups()[0], '<a href="'+target.get_absolute_url()+'">'+smart_unicode(target)+'</a>')
        
    return contents
    
# views
def version_response(request, v):
    return render_to_response(request, 'documents/version.html', {'version': v, 'document': v.document, 'owner':get_owner(v.document)})
    
def view_latest(request, document_id):
    v = get_latest(document_id)
    check_access(request.user, obj=v.document, command='view')
    if v == None:
        raise Http404
    return version_response(request, v)
    
def view_version(request, version_id, document_id):
    v = get_object_or_404_and_check_access(request, Version, pk=version_id, command='view')
    check_access(request.user, obj=v.document, command='view')
    #if v.document.id != document_id:
    #    raise something
    return version_response(request, v)
    
def view_version_list(request, document_id):
    document = get_object_or_404_and_check_access(request, Document, pk=document_id, command='view')
    return render_to_response(request, 'documents/version_list.html', {'version_list': Version.objects.filter(document=document_id), 'document': Document.objects.get(pk=document_id)})

def add_document(request):
    is_presentation = get_boolean(request,'is_presentation')
    owner_group = None
    owner_user = None
    
    class DocumentForm(django.forms.Form):
        title = django.forms.CharField(max_length=1024, label=_('Title'))
        #labels = django.forms.CharField(required=False, label=_('Labels'))
        contents = django.forms.CharField(required=False, widget = django.forms.Textarea, label=_('Contents'))

    group_id = get_integer(request,'group_id')
    user_id = get_integer(request,'user_id')
    if group_id:    
        owner_group = get_object_or_404_and_check_access(request, Group, pk=group_id, command='add')
        check_access(request.user, obj=owner_group, command='add document')
    else:
        owner_user = get_object_or_404_and_check_access(request, User, pk=user_id, command='add')
        check_access(request.user, obj=owner_user, command='add document')       

    if request.POST:
        form = DocumentForm(request.POST)
        
        if form.is_valid():

            #Handle the document
            if owner_group != None:
                document = Document.objects.create(owner_group=owner_group, owner_user=owner_user, is_presentation=is_presentation)
            else:
                document = Document.objects.create(owner_user=owner_user, is_presentation=is_presentation)

            if document.is_presentation:
                if group == 0:
                    title = owner_user.username + 's Presentation'
                else:
                    owner_group = get_object_or_404_and_check_access(request, Group, pk=group, command='add')
                    title = owner_group.name + 's Presentation'
            else:
                title = form.cleaned_data['title']
            
            new_version = Version(document=document,title=title, contents=strip_p(form.cleaned_data['contents']), owner=request.user)
            new_version.save()
            
            #Handle the labels
            #handle_labels(request,document)

            if document.is_presentation:
                if document.owner_group:
                    return HttpResponseRedirect(document.owner_group.get_absolute_url())
                else:
                    return HttpResponseRedirect(document.owner_user.get_absolute_url())
            return HttpResponseRedirect(document.get_absolute_url())

    else:
        form = DocumentForm()

    return render_to_response(request, 'documents/add.html', {'form':form})

def edit_document(request, document_id, is_creating=False):
    group_id = get_integer(request, 'group_id')
    document = get_object_or_404_and_check_access(request, Document, pk=document_id, command='edit')
    user = request.user

    class DocumentForm(django.forms.Form):
        if not document.is_presentation:
            title = django.forms.CharField(max_length=1024, label=_('Title'))
        #labels = django.forms.CharField(required=False, label=_('Labels'))
        contents = django.forms.CharField(required=False, widget = django.forms.Textarea, label=_('Contents'))
        edit_version = django.forms.IntegerField(widget = django.forms.HiddenInput, required=True)
    
    if request.POST:
        form = DocumentForm(request.POST)

        if int(request.POST['edit_version']) != document.get_latest_version().id:
            post = request.POST.copy()
            post['edit_version'] = document.get_latest_version().id
            form = DocumentForm(post)
            form.errors['contents'] = [_('Document was changed after you began editing it, please review the changes and then press save again')]

        if form.is_valid():
            #Handle the labels
            #handle_labels(request,document)
            
            #Handle the document 
            if not document.is_presentation:
                if form.cleaned_data.has_key('title'):
                    title = form.cleaned_data['title']
                else:
                    title = document.get_latest_version().title
            else:
                if user.first_name.endswith('s'):
                    title=user.first_name+' presentation'
                else:
                    title = user.first_name+'s presentation'
            
            new_version = Version(document=document,title=title, contents=strip_p(form.cleaned_data['contents']), owner=request.user)
            new_version.save()
            
            if request.external:
                from curia.homepage.models import MenuItem
                try:
                    menu = MenuItem.objects.get(content_type=get_content_type(document), object_id=document.id)
                    menu.title = title
                    menu.save()
                except MenuItem.DoesNotExist:
                    pass
            
            if document.is_presentation:
                if document.owner_group:
                    return HttpResponseRedirect(document.owner_group.get_absolute_url())
                else:
                    return HttpResponseRedirect(document.owner_user.get_absolute_url())
            return HttpResponseRedirect(document.get_absolute_url())

    else:
        latest_version = document.get_latest_version()
        form = DocumentForm(initial={'title': latest_version.title, 'contents': latest_version.contents, 'edit_version':latest_version.id})

    return render_to_response(request, 'documents/edit.html', {'form':form, 'document':document})
            
def delete_document(request, document_id):
    document = get_object_or_404_and_check_access(request, Document, pk=document_id, command='delete')
    
    from curia import delete_objects
    delete_objects(document)    
    
    if request.external:
        from curia.homepage.models import MenuItem
        try:
            menu = MenuItem.objects.get(content_type=get_content_type(document), object_id=document.id)
            menu.delete()
        except MenuItem.DoesNotExist:
            pass
        
    return HttpResponse(dumps(document_id, ensure_ascii=False), mimetype="text/json; charset=UTF-8")
    
def view_documents_of_user(request, user_id):
    user = get_object_or_404_and_check_access(request, User, pk=user_id, command='view')
    objects = get_objects_from(Document, deleted=False, owner_user=user, owner_group=None, is_presentation=False)
    
    return render_to_response(request, 'documents/document_list.html', {'owner':user, 'objects':objects, 'type':'users'})
    
def view_documents_of_group(request, group_id=None):
    if group_id != None:
        group = get_object_or_404_and_check_access(request, Group, pk=group_id, command='view')
    else:
        group = get_current_community()
    objects = get_objects_from(Document, deleted=False, owner_group=group, is_presentation=False)

    return render_to_response(request, 'documents/document_list.html', {'owner':group, 'objects':objects, 'type':'groups'})
    
def revert_to_version(request, document_id, version_id):
    old_version = Version.objects.get(pk = version_id)
    document = Document.objects.get(pk = document_id)
    new_version = Version(document=document,title=old_version.title, contents=old_version.contents, owner=request.user)
    new_version.save()

    return version_response(request, new_version)    
