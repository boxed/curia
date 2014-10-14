import base64
from datetime import datetime
from sets import Set
from curia.forms import *

from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext as _
from django.utils.encoding import smart_unicode
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseRedirect
from curia.images.models import Image, ImageSet
from curia.shortcuts import *
from curia import *
from curia.labels import *
from curia.labels import get_labels
from curia.labels.models import Label
from curia.labels import handle_labels, mark_labels_as_deleted
from curia.authentication.models import UserPermission
import zipfile

def view_image(request, image_id):
    image = get_object_or_404_and_check_access(request, Image, pk=image_id, command='view')
    return render_to_response(request, 'images/view.html', {'image': image, 'owner': get_owner(image)})
    
def add_image(request, set_id):
    image_set = get_object_or_404_and_check_access(request, ImageSet, pk=set_id, command='view')
    owner_group = image_set.owner_group
    user = request.user

    class AddForm(django.forms.Form):
        #title = django.forms.CharField(label=_('Title'))
        description = django.forms.CharField(required=False, widget = django.forms.Textarea, label=_('Description'))
        #labels = django.forms.CharField(required=False, label=_('Labels'))
        image = django.forms.ImageField(required=False, label=_('image'))

    if request.POST:
        new_data = request.POST.copy()
        new_data.update(request.FILES)
        form = AddForm(new_data)
        
        valid_extensions = ['jpg', 'jpeg', 'gif', 'bmp', 'png', 'tif', 'tiff']
        if form.is_valid() and not image_set.deleted:
            if 'image' in new_data:  
                image = None
                if not new_data['image'].name.lower().endswith(".zip"):
                    name, extension = new_data['image'].name.rsplit('.', 1)
                    extension = extension.lower()
                    if extension in valid_extensions:
                        image = Image.objects.create(owner_user=request.user,owner_group=owner_group,description=form.cleaned_data['description'])
                        save_file_for_object(obj=image, fieldname='image', data=new_data)
                        image_set.images.add(image)
                        image_set.number_of_images += 1
                else:
                    import os
                    temp_name = os.tempnam()
                    temp_file = open(temp_name,'wb')
                    temp_file.write(new_data['image']['content'])
                    temp_file.close()
                    try:
                        zf = zipfile.ZipFile(temp_name)
                        for info in zf.infolist():
                            if not info.file_size == 0 and not '/._' in info.filename:
                                name, extension = info.filename.rsplit('.', 1)
                                extension = extension.lower()
                                if extension in valid_extensions:
                                    image = Image.objects.create(owner_user=request.user,owner_group=owner_group,description=form.cleaned_data['description'])
                                    def read_the_file():
                                        return zf.read(info.filename) 
                                    new_data['image'].read = read_the_file
                                    new_data['image'].name = info.filename                                                  
                                    save_file_for_object(obj=image, fieldname='image', data=new_data)
                                    image_set.images.add(image)
                                    image_set.number_of_images += 1
                        temp_file.close()
                        try:
                            os.remove(temp_name)
                        except:
                            pass
                    except zipfile.BadZipFile:
                        form.errors['image'] = [_('Invalid zip file')]
                        return render_to_response(request, 'images/add.html', {'form':form})

                image_set.save()
                
                #Set an image as representative
                if image_set.representative_image is None and image != None:
                    image_set.representative_image = image
                    image_set.save()
                    
            return HttpResponseRedirect(image_set.get_absolute_url())
    else:
        form = AddForm(initial={})
        
    return render_to_response(request, 'images/add.html', {'form':form})
    
def edit_image(request, image_id):
    image = Image.objects.get(pk=image_id)
    check_access(request.user, image.sets.all()[0], command='view')
    
    class EditForm(django.forms.Form):
        description = django.forms.CharField(required=False, widget = django.forms.Textarea, label=_('Description'))
        #labels = django.forms.CharField(required=False, label=_('Labels'))
    
    try: 
        owner_group = image.owner_group
    except:
        owner_group = None
    
    if request.POST:
        form = EditForm(request.POST)

        if form.is_valid():
            #Handle the labels
            #handle_labels(request,image, owner_group)

            image.description = form.cleaned_data['description']
            image.save()
            return HttpResponseRedirect(image.sets.all()[0].get_absolute_url())
    else:
        form = EditForm({'description':image.description})
                
    return render_to_response(request, 'images/edit.html', {'form':form, 'image':image})
        
def delete_image(request, image_id):
    image = Image.objects.get(pk=image_id)
    check_access(request.user, image.sets.all()[0], command='view')
    delete_object(image)
    
    #If this was the representative, set another image as representative
    image_set = image.sets.all()[0]
    if image_set.representative_image == image:
        try:
            image_set.representative_image = Image.objects.filter(sets=image_set, deleted=False)[0]
        except:
            image_set.representative_image = None
    image_set.number_of_images -= 1
    image_set.save()
                        
    mark_labels_as_deleted(image, request.user)

    from django.utils.simplejson import dumps 
    return HttpResponse(dumps(image.id, ensure_ascii=False), content_type="text/json; charset=UTF-8")

def view_sets_of_group(request, group_id=None, page=None):
    if group_id != None:
        group = get_object_or_404_and_check_access(request, Group, pk=group_id, command='view')
    else:
        group = get_current_community()
    sets = ImageSet.objects.filter(owner_group=group, deleted=False)
    check_access(request.user, group, command='view')
    
    try:
        page_size = int(request.GET['page_size'])
    except:
        page_size = 6 # get from user settings
    
    paginator = Paginator(sets, page_size)

    number_of_pages = paginator.num_pages
    got_page_size = False

    if number_of_pages != 0:
        if not page:
            page = 1
        page = int(page)
        # TODO: implement getting page ranges
        #end_page = int(request.GET['end_page'])
        end_page = page
        sets = paginator.page(page)
    else:
        end_page = 0
        page = 0
        sets = []
    
    next_page = page+1
    has_next_page = paginator.page(page).has_next()
    
    return render_to_response(request, 'images/view_sets.html', {'owner':group, 'sets':sets, 'is_paginated':True, 'base_url':'/images/groups/'+str(group.id)+'/sets/', 'number_of_pages':number_of_pages, 'page':page, 'end_page':end_page, 'has_next_page':has_next_page, 'has_previous_page':paginator.page(page).has_previous(), 'next_page':next_page, 'previous_page':page - 1, 'page_size':page_size,'paginator':paginator})
    
def view_set(request, set_id, page=None):
    image_set = get_object_or_404_and_check_access(request, ImageSet, pk=set_id, command='view')
    images = Image.objects.filter(sets=image_set, deleted=False)
    
    #try:
        #page_size = int(request.GET['page_size'])
    #except:
        #page_size = 2 # get from user settings
        
    #paginator = Paginator(images, page_size)

    #number_of_pages = paginator.num_pages
    #got_page_size = False

    #if number_of_pages != 0:
        #if not page:
            #page = 1
        #page = int(page)
        # TODO: implement getting page ranges
        #end_page = int(request.GET['end_page'])
        #end_page = page
        #images = paginator.page(page)
    #else:
        #end_page = 0
        #page = 0
        #images = []
    
    #next_page = page+1
    #has_next_page = paginator.page(page).has_next()    
    return render_to_response(request, 'images/view_set.html', {'owner':get_owner(image_set), 'images':images, 'set':image_set, 'numer_of_images':image_set.number_of_images, 'user':request.user})
    
def edit_set(request, set_id, group_id=None):
    if group_id != None:
        group = get_object_or_404_and_check_access(request, Group, pk=group_id, command='view')
    else:
        group = get_current_community()
    image_set = ImageSet.objects.get(pk=set_id)
    check_access(request.user, image_set, command='view')

    class EditForm(django.forms.Form):
        title = django.forms.CharField(label=_('Album title'), help_text=_('The title will be visible in the set list'))
        labels = django.forms.CharField(required=False, label=_('Labels'), help_text=_('Help your friends find this item'))  
        description = django.forms.CharField(required=False, widget = django.forms.Textarea, label=_('Description'))

    if request.POST:
        form = EditForm(request.POST)

        if form.is_valid():
            image_set.title = form.cleaned_data['title']
            image_set.description = form.cleaned_data['description']
            image_set.save()
            
            #Handle the labels
            handle_labels(request,image_set,group)
            return HttpResponseRedirect(image_set.get_absolute_url())

    else:
        form = EditForm({'title':image_set.title, 'description':image_set.description, 'labels': ', '.join([unicode(label) for label in get_labels(image_set)])})
        
    return render_to_response(request, 'images/edit_set.html', {'owner':get_owner(image_set), 'set':image_set, 'form':form})
    
def add_set(request, group_id=None):
    if group_id != None:
        group = get_object_or_404_and_check_access(request, Group, pk=group_id, command='add')
    else:
        group = get_current_community()
    check_access(request.user, group, command='view')

    class AddForm(django.forms.Form):
        title = django.forms.CharField(label=_('Album title'), help_text=_('The title will be visible in the set list'))
        labels = django.forms.CharField(required=False, label=_('Labels'), help_text=_('Help your friends find this item'))  
        description = django.forms.CharField(required=False, widget = django.forms.Textarea, label=_('Description'))

    if request.POST:
        form = AddForm(request.POST)

        if form.is_valid():
            image_set = ImageSet.objects.create(title = form.cleaned_data['title'], description = form.cleaned_data['description'], owner_user = request.user, owner_group = group)

            #Handle the labels
            handle_labels(request,image_set,group)
            
            return HttpResponseRedirect(image_set.get_absolute_url())
    
    else:
        form = AddForm(initial={})
        print form.fields
        
    return render_to_response(request, 'images/add_set.html', {'form':form})
    
def edit_representative_image(request, set_id, image_id):  
    image_set = ImageSet.objects.get(pk=set_id)
    image = Image.objects.get(pk=image_id)
    check_access(request.user, image_set, command='view')
    images = Image.objects.filter(sets=image_set, deleted=False)

    image_set.representative_image = image
    image_set.save()
    
    return HttpResponseRedirect(image_set.get_absolute_url())
    
def delete_image_set(request, set_id):
    image_set = ImageSet.objects.get(pk=set_id)
    check_access(request.user, image_set, command='change set')
    delete_object(image_set)

    for image in Image.objects.filter(sets=image_set, deleted=False):
        delete_object(image)

    from django.utils.simplejson import dumps 
    return HttpResponse(dumps(image_set.owner_group.id, ensure_ascii=False), content_type="text/json; charset=UTF-8")