from curia.shortcuts import *
from curia import *
from curia.homepage.models import *

from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _
from curia.authentication import *

def admin_index(request):
    if request.community == None:
        return render_to_response(request, '404_community.html')

    check_perm(request.user, request.community, 'administrate homepage')
    return render_to_response(request, 'homepage/admin_index.html')

def overview(request):
    check_perm(request.user, request.community, 'administrate homepage')
    menus = MenuItem.objects.filter(group=request.community, parent__isnull=True)
    return render_to_response(request, 'homepage/overview.html', {'menus':menus})

def add_menu_item(request):
    check_perm(request.user, request.community, 'administrate homepage')
    owner_group = request.community
    owner_user = request.user
    
    choices = [(None, _('<No parent>'))]
    choices.extend([(x.id,x.title) for x in MenuItem.objects.filter(group=owner_group, parent__isnull=True)])
    
    class MenuForm(django.forms.Form):
        parent = django.forms.ChoiceField(required=False, choices=choices)
        title = django.forms.CharField(required=True, label=_('Title'))
        contents = django.forms.CharField(required=False, widget = django.forms.Textarea, label=_('Text'))

    if request.POST:
        form = MenuForm(request.POST)
        
        if form.is_valid():
            from curia.documents.models import Document, Version
            from curia.authentication import grant_access, get_public_user
            
            # create document
            document = Document.objects.create(owner_group=owner_group, owner_user=owner_user, is_presentation=False)
            new_version = Version(document=document,title=form.cleaned_data['title'], contents=form.cleaned_data['contents'], owner=request.user)
            new_version.save()
            
            # set up access rights
            grant_access(command='view', user=get_public_user(), obj=document)
            
            # create menu item
            parent = None
            if form.cleaned_data['parent'] != 'None':
                parent = MenuItem.objects.get(pk=form.cleaned_data['parent'])
            MenuItem.objects.create(group=owner_group, content_type=get_content_type(document), object_id=document.id, title=form.cleaned_data['title'], url=document.get_absolute_url(), order=0, parent=parent)
            
            return HttpResponseRedirect("/")
    else:
        initial = {}
        if MenuItem.objects.count() == 0:
            initial['title'] = _('Home')
        form = MenuForm(initial=initial)
    
    return render_to_response(request, 'homepage/add_menu_item.html', {'form':form})