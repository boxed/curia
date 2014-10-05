from curia.authentication import *
from curia.authentication.models import *
from curia.documents.models import *
from curia.notifications.models import *
from curia.shortcuts import *
from curia.labels import get_labels
from curia.labels import handle_labels
from curia.notifications import *
from curia.authentication import check_access
from curia.notifications.models import SubscriptionResult
from django.contrib.auth import authenticate
from django.core.validators import EmailValidator
from django.http import HttpResponseRedirect
from django.template.defaultfilters import capfirst
from django.core.paginator import Paginator
from django.utils.translation import ugettext as _
import django.forms

def get_presentation_for_user(user, community):
    try:    
        presentation = Document.objects.get(owner_user=user, owner_group=community, is_presentation=True)
    except Document.DoesNotExist:
        # this is a brand new user, so we need to set some initial data
        # create presentation
        presentation = Document.objects.create(owner_user=user, owner_group=community, is_presentation=True)
        new_version = Version(document=presentation,title='presentation', contents=_('Write a presentation why don\'t ya?'), owner=user)
        new_version.save()
    return presentation
    
class LoginForm(django.forms.Form):
    username = django.forms.CharField(max_length=1024, label=_('Email'))
    password = django.forms.CharField(max_length=1024,widget = django.forms.PasswordInput, label=_('Password'))

def login(request, template='authentication/login.html'):
    community = request.community
    try:
        next = request.REQUEST['next']
    except:
        next = ''
    if next == '':
        next = '/'
    
    if community == None:
        return render_to_response(request, '404_community.html')
        
    if request.POST:
        form = LoginForm(request.POST)
        if form.is_valid():            
            try:
                username = User.objects.get(email=form.cleaned_data['username']).username
                user = authenticate(username=username, password=form.cleaned_data['password'])
            except:
                user = None
            if user == None:
                form.errors['username'] = [_(u'Username or password incorrect')]
            else:
                is_member = hasattr(community, 'user_set') and user in community.user_set.all() or user.is_superuser
                if unicode(community).lower() != 'eldmyra' and not is_member:
                    form.errors['username'] = [_(u'You are not a member of %s') % community]
                else:
                    if user is not None and user.is_active:
                        from django.contrib.auth import login
                        login(request, user)
                        
                        try:
                            if user.meta.language != '':
                                request.session['django_language'] = user.meta.language
                            else:
                                from django.conf import settings
                                request.session['django_language'] = settings.LANGUAGE_CODE
                            meta = user.meta
                            meta.last_notification_email_time = None
                            meta.save()
                        except MetaUser.DoesNotExist:
                            pass
                            
                        if not is_member:
                            communities = user.groups.exclude(name='everyone')
                            if len(communities) == 1:
                                return HttpResponseRedirect(communities[0].get_absolute_url())
                            return render_to_response(request, 'community_selector_login.html', {'communities':communities, 'login_form':None})
                        else:
                            if next == '/':
                                next = community.get_absolute_url()
                            return HttpResponseRedirect(next)
    else:
        form = LoginForm(initial={})
        
    return render_to_response(request, template, {'login_form': form, 'next':next})
    
        
def logout(request):
    from django.contrib.auth import logout
    logout(request)
    return HttpResponseRedirect('http://%s/' % request.domain)
    
def edit_user(request, user_id):
    user = get_object_or_404_and_check_access(request, User, pk=user_id, command='edit')
    try:
        meta_user = user.meta
    except MetaUser.DoesNotExist:
        from django.http import Http404
        raise Http404
    #group = Group.objects.get(name='friends of '+user.username)
    presentation = get_presentation_for_user(user, request.community)
    
    details = Detail.objects.filter(owner_user=user).exclude(name='display name').order_by('id')
    
    class EditForm(django.forms.Form):
        presentation = django.forms.CharField(widget = django.forms.Textarea,required=False, label=_('Presentation text'))
        picture = django.forms.ImageField(required=False, label=_('Picture'))
        no_picture = django.forms.BooleanField(required=False, label=_('Remove my picture'))

    if request.POST:
        new_data = request.POST.copy()
        new_data.update(request.FILES)
        form = EditForm(new_data)

        if form.is_valid():
            django.forms.models.save_instance(form, meta_user)
            
            if form.cleaned_data['picture'] is not None:  
                save_file_for_object(obj=meta_user, fieldname='picture', data=new_data)
            meta_user.save()
            name = user.username
            
            new_version = Version(document=presentation,title='Presentation', contents=strip_p(form.cleaned_data['presentation']), owner=user)
            new_version.save()
            
            # remove presentation picture if wanted
            if form.cleaned_data['no_picture']:
                meta_user.picture = u'user-pictures/default_user_image.png'
                meta_user.thumbnail = u'user-thumbnails/default_user_image.png'
                meta_user.icon = u'user-icons/default_user_image.png'                
                meta_user.save()
            
        return HttpResponseRedirect(str(user.get_absolute_url()))
    else:
        form = EditForm(initial={'birthday': meta_user.birthday, 'username': user.username, 'presentation':presentation.get_latest_version().contents,'labels': ', '.join([unicode(label) for label in get_labels(user)])})
    return render_to_response(request, 'authentication/edit_user.html', {'form':form, 'the_user': user, 'details': details, 'viewer':request.user})

def edit_user_settings(request, user_id):
    user = User.objects.get(pk=user_id)
    
    if user != request.user and request.user.is_superuser == False:
        return HttpResponseRedirect('/')   
    
    meta = user.meta
           
    class EditForm(django.forms.Form):
        firstname = django.forms.CharField(label=_('First name'), help_text=_('Visible to other users'))
        lastname = django.forms.CharField(required=False, label=_('Last name'), help_text=_('Visible to other users'))    
        email = django.forms.CharField(label=_('E-mail'), help_text=_('Not visible to other users'))
        birthday = django.forms.DateField(required=False, label=_('Birthday'), help_text=_('Format is yyyy-MM-dd, e.g. 1980-05-27'))
        #language = django.forms.ChoiceField(label=_('Language'), choices=(('en-us', 'English'), ('sv-se', 'Svenska'),))
        gender = django.forms.ChoiceField(label=_('Gender'), choices=(('M', _('Male')), ('F', _('Female')),), help_text=_('Visible to other users'))
        old_password = django.forms.CharField(label=_('Password'), widget = django.forms.PasswordInput, help_text=_('Confirm your identity'))
        #new_password = django.forms.CharField(label=_('Password'), widget = django.forms.PasswordInput, required=False)
        #confirm = django.forms.CharField(label=_('Confirm password'), widget = django.forms.PasswordInput, required=False)
        #location = django.forms.ChoiceField(label=_('Location'), choices=(('Stockholm', 'Stockholm'), ('Inte Stockholm', 'Inte Stockholm'),))
        notification_style = django.forms.ChoiceField(label=_('Notification style'), choices=user.meta.NotificationStyle_Choices)
        
        # TODO: first day of week
    error = ''
    if request.POST:
        form = EditForm(request.POST)
        if form.data['firstname'].isspace():
            form.data['firstname'] = None
        if not user.check_password(form.data['old_password']):
            form.errors['old_password'] = (_('Incorrect password'),)

        email = form.data["email"]
        if email != '':
            if not EmailValidator(email):
                form.errors['email'] = (_('%s is not a valid email address') % email,)
        
        try:
            existing_user = User.objects.get(email=form.data['email'])
        except User.DoesNotExist:
            existing_user = None
        if existing_user and existing_user != user:
            form.errors['email'] = _('The selected e-mail address was invalid.')

        if form.is_valid():
            user.first_name = form.cleaned_data['firstname']
            user.last_name = form.cleaned_data['lastname']
            user.save()
            user.email = form.cleaned_data['email']
            user.save()
            meta.notification_style = form.cleaned_data['notification_style']
            
            django.forms.models.save_instance(form, meta)
                        
            request.session['django_language'] = user.meta.language
       
            return HttpResponseRedirect(str(user.get_absolute_url()))     
    else:
        form = EditForm(initial={
            'birthday': meta.birthday, 
            'gender':meta.gender, 
            'username':user.username, 
            'firstname': user.first_name, 
            'lastname': user.last_name, 
            'email':user.email, 
            'language':user.meta.language,
            'first_name':user.first_name, 
            'last_name':user.last_name,
            'notification_style':meta.notification_style,
            })
        
    return render_to_response(request, 'authentication/edit_user_settings.html', {'form':form, 'the_user': user})

def edit_user_password(request, user_id=None):
    if user_id != None:
        user = User.objects.get(pk=user_id)
    else:
        user = request.user
    
    if user != request.user and request.user.is_superuser == False:
        return HttpResponseRedirect('/')

    class EditForm(django.forms.Form):
        new_password = django.forms.CharField(label=_('Password'), widget = django.forms.PasswordInput, required=False, help_text=_('Your new password'))
        confirm = django.forms.CharField(label=_('Confirm password'), widget = django.forms.PasswordInput, required=False, help_text=_('Confirm your new password'))
        old_password = django.forms.CharField(label=_('Old password'), widget = django.forms.PasswordInput, help_text=_('Confirm your identity'))

    if request.POST:
        form = EditForm(request.POST)
        if not user.check_password(form.data['old_password']):
            form.errors['old_password'] = (_('Incorrect password'),)

        if form.data['new_password'] != form.data['confirm'] and form.data['confirm'] != '':
            form.errors['confirm'] = (_('Passwords did not match.'),)

        if form.is_valid():
            if form.cleaned_data['confirm'] != '':
                user.set_password(form.cleaned_data['new_password'])
            user.save()

            return HttpResponseRedirect(str(user.get_absolute_url()))     
    else:
        form = EditForm(initial={})

    return render_to_response(request, 'authentication/edit_user_password.html', {'form':form, 'the_user': user})
    
def view_user(request, user_id):
    user = get_object_or_404_and_check_access(request, User, pk=user_id, command='view')
    if user in request.community.user_set.all():
        in_community = True
    else:
        in_community = False
        
    presentation = get_presentation_for_user(user, request.community)
        
    if user.meta.birthday:
        user_age = age(user.meta.birthday)
    else:
        user_age = ''
        
    presentation = presentation.get_latest_version().contents

    return render_to_response(request, 'authentication/view_user.html', {'presentation':presentation, 'current_user':user, 'age':user_age, 'in_community':in_community, 'group':request.community})
    
def view_members(request, group_id=None, page=None):
    if group_id:
        group = get_object_or_404_and_check_access(request, Group, pk=group_id, command='view')
    else:
        group = request.community
    
    members = group.user_set.order_by('first_name', 'last_name')   

    try:
        page_size = int(request.GET['page_size'])
    except:
        page_size = 12 # get from user settings

    paginator = Paginator(members, page_size)

    number_of_pages = paginator.num_pages
    got_page_size = False

    if number_of_pages != 0:
        if not page:
            page = 1
        page = int(page)
        # TODO: implement getting page ranges
        #end_page = int(request.GET['end_page'])
        end_page = page
        members = paginator.page(page)
    else:
        end_page = 0
        page = 0
        members = []

    next_page = page+1
    has_next_page = paginator.page(page).has_next()

    return render_to_response(request, 'authentication/view_members.html', {
        'group': group, 
        'members': members, 
        'user_in_group':request.user in group.user_set.all(), 
        'is_paginated':True, 
        'base_url':'/groups/'+str(group.id)+'/members/', 
        'number_of_pages':number_of_pages, 
        'page':page, 
        'end_page':end_page, 
        'has_next_page':has_next_page, 
        'has_previous_page':paginator.page(page).has_previous(), 
        'next_page':next_page, 
        'previous_page':page - 1, 
        'page_size':page_size,
        'paginator':paginator
    })
   
def add_group(request):
    meta_community = request.community.meta
    class GroupForm(django.forms.Form):
        name = django.forms.CharField(label=_('Name'))
        #labels = django.forms.CharField(required=False, label=_('Labels'))
        #logo = django.forms.ImageField(widget = django.forms.FileInput, required=False, label=_('Logo'))

    check_access(request.user, command='add group')
    error = 0
    
    if request.POST:
        new_data = request.POST.copy()
        new_data.update(request.FILES)
        form = GroupForm(new_data)

        if form.is_valid():
           
            error = None
            if error == None:
                try:
                    new_group = Group.objects.create(name=form.cleaned_data['name'])
                    meta_group = MetaGroup.objects.create(group=new_group, created_by=request.user)
                    meta_community.children.add(meta_group)
                    meta_community.save()
                    content_type = get_content_type(new_group)
                except:
                    error = _("There is already a group with this name. Please choose another one.")
           
            if error == None:
                try:
                    presentation = Document.objects.get(owner_group=new_group, owner_user__isnull=True, is_presentation=True)
                except Document.DoesNotExist:
                    presentation = Document.objects.create(owner_group=new_group, is_presentation=True)
                    name = new_group.name
                    if name.endswith('s'):
                        title=new_group.name+' presentation'
                    else:
                        title = new_group.name+'s presentation'
                    new_version = Version(document=presentation,title=title, contents=_('Write a presentation why don\'t ya?'), owner=request.user)
                    new_version.save() 
                    watcher = Watcher(user=request.user, owner_group=new_group, inverse=False)
                    watcher.save()

                django.forms.models.save_instance(form, meta_group)
                new_group.user_set.add(request.user)
                UserPermission.objects.create(user=request.user, command='add', content_type=get_content_type(new_group), object_id=new_group.id)
                UserPermission.objects.create(user=request.user, command='delete', content_type=get_content_type(new_group), object_id=new_group.id)
                UserPermission.objects.create(user=request.user, command='view', content_type=get_content_type(new_group), object_id=new_group.id)
                UserPermission.objects.create(user=request.user, command='edit', content_type=get_content_type(new_group), object_id=new_group.id)
   
                #Handle the labels
                handle_labels(request,new_group)
   
                return HttpResponseRedirect('/administration/')
    
            return render_to_response(request, 'authentication/add_group.html', {'form':form, 'error':error}) 

    else:
        form = GroupForm()

    return render_to_response(request, 'authentication/add_group.html', {'form':form})    
    
def edit_group(request, group_id=None):
    if group_id != None:
        group = get_object_or_404_and_check_access(request, Group, pk=group_id, command='edit')
    else:
        group = get_current_community()
    meta_group = group.meta
    details = Detail.objects.filter(owner_group=group)
    presentation = Document.objects.get(owner_group=group, owner_user__isnull=True, is_presentation=True)

    class EditForm(django.forms.Form):
        presentation = django.forms.CharField(widget = django.forms.Textarea,required=False, label=_('Presentation text'))
        
    if request.POST:
        new_data = request.POST.copy()
        new_data.update(request.FILES)
        form = EditForm(new_data)
    
        if form.is_valid():
            error=None

            if error == None:
                title = group.name+'s presentation'        
                new_version = Version(document=presentation,title=title, contents=form.cleaned_data['presentation'], owner=request.user)
                new_version.save()

                return HttpResponseRedirect('/')
        
        else:
            error=None
        return render_to_response(request, 'authentication/edit_group.html', {'form':form, 'group': group, 'error':error, 'presentation':presentation.get_latest_version().contents})
    else:
        form = EditForm(initial={'presentation':presentation.get_latest_version().contents})

    return render_to_response(request, 'authentication/edit_group.html', {'form':form, 'group': group, 'details': details})    

def get_simple_permission_level(group):
    access_type = 'closed'
    if GroupPermission.objects.filter(group=get_everyone_group(), command='view', deny=True, content_type=get_content_type(group), object_id=group.id).count() != 0:
        access_type = 'hidden'
    elif UserPermission.objects.filter(user=get_public_user(), command='view', deny=False, content_type=get_content_type(group), object_id=group.id).count() != 0:
        access_type = 'open'
    return access_type
        
def view_permissions(request, object_id, type):
    content_type = get_content_type(type)
    obj = get_object_or_404_and_check_access(request, content_type.model_class(), pk=object_id, command='view')
    check_perm(request.user, obj, 'edit')
    owner = get_owner(obj)
    
    from curia.authentication.models import GroupPermission, UserPermission
    
    class PermissionForm(django.forms.Form):
        access_type = django.forms.ChoiceField(choices=[('hidden',_('Hidden')), ('closed',_('Closed')), ('open',_('Open'))], widget = django.forms.RadioSelect)
        external_editing = django.forms.BooleanField(required=False)
        blocked_users = django.forms.CharField(widget = django.forms.Textarea, required=False)
        
    access_type = 'closed'
    if request.method == 'POST':
        form = PermissionForm(request.POST)
        
        # TODO: validate blocked users
        
        if form.is_valid():
            # clean old data
            GroupPermission.objects.filter(content_type=content_type, object_id=object_id).delete()
            UserPermission.objects.filter(content_type=content_type, object_id=object_id).delete()
            
            # set the new stuff
            access_type = form.cleaned_data['access_type']
            if access_type == 'hidden':
                if isinstance(obj, Group):
                    GroupPermission.objects.create(group=get_everyone_group(), command='view', deny=True, content_type=content_type, object_id=object_id)
                    GroupPermission.objects.create(group=obj, command='view', deny=False, content_type=content_type, object_id=object_id)
                    GroupPermission.objects.create(group=obj, command='add', deny=False, content_type=content_type, object_id=object_id)
                    GroupPermission.objects.create(group=obj, command='change', deny=False, content_type=content_type, object_id=object_id)
            elif access_type == 'open':
                if isinstance(obj, Group):
                    GroupPermission.objects.create(group=get_everyone_group(), command='view', deny=False, content_type=content_type, object_id=object_id)
                    GroupPermission.objects.create(group=get_everyone_group(), command='add', deny=False, content_type=content_type, object_id=object_id)
                    GroupPermission.objects.create(group=get_everyone_group(), command='join', deny=False, content_type=content_type, object_id=object_id)
                    UserPermission.objects.create(user=get_public_user(), command='view', deny=False, content_type=content_type, object_id=object_id)
            else: # closed
                pass # this is the default
            
            for username in split_and_trim(form.cleaned_data['blocked_users']):
                UserPermission.objects.create(user=User.objects.get(username=username), command='view', deny=True, content_type=content_type, object_id=object_id)
            
            if form.cleaned_data['external_editing']:
                GroupPermission.objects.create(group=get_everyone_group(), command='change', deny=False, content_type=content_type, object_id=object_id)
    else:
        if type == Group:    
            access_type = get_simple_permission_level(obj)
        elif type != User and obj.owner_group != None:
            access_type = get_simple_permission_level(obj.owner_group)
        
        # blocked_users: users with deny read
        blocked_users = u', '.join([unicode(permission.user) for permission in UserPermission.objects.filter(command='view', deny=True, content_type=content_type, object_id=object_id)])
        
        # external_editing: everyone is granted edit rights
        external_editing = GroupPermission.objects.filter(group=get_everyone_group(), command='edit', deny=False, content_type=content_type, object_id=object_id).count() != 0
        form = PermissionForm(initial={'access_type':access_type, 'blocked_users':blocked_users, 'external_editing':external_editing})
    return render_to_response(request, 'authentication/view_permissions.html', {'form':form, 'obj':obj, 'content_type':content_type, 'owner':owner, 'access_type':access_type})

def view_advanced_permissions(request, object_id, type):
    content_type = get_content_type(type)
    obj = get_object_or_404_and_check_access(request, content_type.model_class(), pk=object_id, command='view')
    check_perm(request.user, obj, 'edit')
    errors = []
    
    available_commands = ['add', 'view', 'edit', 'delete']
    
    class Command:
        def __init__(self, permission, command, b):
            self.permission = permission
            self.command = command
            self.b = b
            
        def __unicode__(self):
            return self.command
        
        def __str__(self):
            return self.command
        
        def enabled(self):
            return self.b
    
    permission_id = 0
    class Permission:
        def __init__(self, permission, id):
            self.permissions = []
            try:
                self.user = permission.user
            except AttributeError:
                self.group = permission.group
            self._commands = {}
            for a in available_commands:
                self._commands[a] = False

            self.add_permission(permission)
            self.id = id
            
        def add_permission(self, permission):
            self.permissions.append(permission)
            self._commands[permission.command] = True
            
        def __unicode__(self):
            return smart_unicode(self._commands)

        def __repr__(self):
            return smart_unicode(self._commands)

        def commands(self):
            return map(lambda x:Command(self, x[0], x[1]), self._commands.items())
            
    if request.method == 'POST':
        UserPermission.objects.filter(content_type=content_type, object_id=object_id).delete()
        GroupPermission.objects.filter(content_type=content_type, object_id=object_id).delete()

        new_data = request.POST.copy()

        def handle_params(key, deny, type):
            if deny:
                type_key = 'deny_'+type
            else:
                type_key = 'accept_'+type
            if key.startswith(type_key+'_name_'):
                id = key[len(type_key+'_name_'):]
                if new_data[key] != "":
                    if type == 'user':
                        try:
                            user = User.objects.get(username=new_data[key])
                        except:
                            error = _('No user with the name %(name)s exists.') % {'name':new_data[key]}
                            errors.append(error)
                    else:
                        try:
                            group = Group.objects.get(name=new_data[key])
                        except:
                            error = _('No group with the name %(name)s exists.') % {'name':new_data[key]}
                            errors.append(error)
                    for command in available_commands:
                        if type_key+'_'+command+'_'+id in new_data:
                            if type == 'user':
                                try:
                                    UserPermission.objects.create(user=user, command=command, content_type=content_type, object_id=object_id, deny=deny)
                                except:
                                    pass
                            else:
                                try:
                                    GroupPermission.objects.create(group=group, command=command, content_type=content_type, object_id=object_id, deny=deny)
                                except:
                                    pass
        for key in new_data.keys():
            handle_params(key, deny=False, type='user')
            handle_params(key, deny=True, type='user')
            handle_params(key, deny=False, type='group')
            handle_params(key, deny=True, type='group')
    
    class Foo:
        pass
            
    permission_structure = Foo
    permission_structure.permission_id = 1
    permission_structure.types = {}
    
    
    def create_permission_structure(permission_structure, deny, type):
        if deny:
            key = 'deny_'
            title = 'Deny '
        else:
            key = 'accept_'
            title = 'Accept '
        key += type
        title += type
        permission_structure.types[key] = {}
        permission_structure.types[key]['type'] = key
        permission_structure.types[key]['title'] = _(title)
        permission_structure.types[key]['label'] = _(capfirst(type))
        permission_structure.types[key]['permissions'] = {}
        
        if type == 'user':
            permissions = UserPermission.objects.filter(content_type=content_type, object_id=object_id, deny=deny)
        else:
            permissions = GroupPermission.objects.filter(content_type=content_type, object_id=object_id, deny=deny)
        for permission in permissions:
            if type == 'user':
                id = permission.user.id
            else:
                id = permission.group.id
            if id in permission_structure.types[key]['permissions']:
                permission_structure.types[key]['permissions'][id].add_permission(permission)
            else:
                permission_structure.types[key]['permissions'][id] = Permission(permission, permission_structure.permission_id)
                permission_structure.permission_id += 1
                
    create_permission_structure(permission_structure, deny=False, type='user')
    create_permission_structure(permission_structure, deny=True, type='user')
    create_permission_structure(permission_structure, deny=False, type='group')
    create_permission_structure(permission_structure, deny=True, type='group')
    
    return render_to_response(request, 'authentication/view_advanced_permissions.html', {'obj':obj, 'available_commands':available_commands, 'types':permission_structure.types, 'next_id':permission_structure.permission_id, 'errors': errors})

def delete_permission(request, permission_id):
    permission = get_object_or_404_and_check_access(request, UserPermission, id=permission_id, command='delete')

    if request.method == 'POST':
        permission.delete()
        return render_to_response(request, 'empty.html')

    raise Exception()     
    
def validate_invites(form, event=None):
    usernames = map(lambda x: x.strip(), form.data['invite_users'].split(','))
        
    users = []
    errors = []
    for username in usernames:
        if username != '':
            try:
                user = User.objects.get(username=username)
                try:
                    Invite.objects.get(user=user)
                except Invite.DoesNotExist:
                    users.append(user)
            except User.DoesNotExist:
                errors.append('no username "%s"' % username)
    
    if len(errors) != 0:        
        form.errors['invite_users'] = errors

    return (users)
    
def handle_invites(inviter, group, users, groups=[]):
    for user in users:
        check_access(user=inviter, obj=user, command='view')
        
        try:
            answer = Invite.objects.get(inviter=inviter, group=group, user=user)
            if answer.choice == "N":
                answer.delete()
                Invite.objects.create(inviter=inviter, group=group, user=user)
        except Invite.DoesNotExist:
            Invite.objects.create(inviter=inviter, group=group, user=user)

def reply_to_invitation(request, group_id=None):
    if group_id != None:
        group = Group.objects.get(pk=group_id)
    else:
        group = get_current_community()
    answer = Invite.objects.get(group=group, user=request.user, choice='-')
    user = answer.user
    
    if 'answer' in request.REQUEST:
        answer.choice = request.REQUEST['answer']
        if group.meta.friend_group:
            if answer.choice == "Y":
                inviter = answer.inviter
                user_friends = Group.objects.get(name="friends of "+user.username)
                group.user_set.add(user)
                user_friends.user_set.add(inviter)
                answer.delete()
                watcher = Watcher(user=user, owner_user=inviter, inverse=False)
                watcher.save()
                watcher = Watcher(user=inviter, owner_user=user, inverse=False)
                watcher.save()
                answer.delete()
            return HttpResponseRedirect(user.get_absolute_url())
        else:
            if answer.choice == "Y":
                for member in group.user_set.all():
                    if member != request.user:
                        SubscriptionResult.objects.create(user=member, content_type=get_content_type(user), object_id=user.pk, originator_user=get_current_user(), originator_group=get_current_community())
                
                group.user_set.add(user)
                answer.save()
                return HttpResponseRedirect(group.get_absolute_url())
            answer.save()
            return HttpResponseRedirect('/')

    return render_to_response(request, 'authentication/reply_to_invitation.html', {'group':group, 'invite':answer})  

def remove_invitation(request, user_id, invited_id):
    # TODO: check access!
    user = User.objects.get(pk=user_id)
    invited_user = User.objects.get(pk=invited_id)
    group = Group.objects.get(name="friends of "+user.username)
    answer = Invite.objects.get(group=group, user=invited_user)
    answer.delete()
    
    return HttpResponseRedirect('/users/'+unicode(user.id)+'/friends/')

def remove_invitation_to_group(request, user_id, group_id=None):
    # TODO: check access!
    if group_id != None:
        group = Group.objects.get(pk=group_id)
    else:
        group = get_current_community()
    invited_user = User.objects.get(pk=user_id)
    answer = Invite.objects.get(group=group, user=invited_user)
    answer.delete()

    return HttpResponseRedirect('/groups/'+unicode(group.id)+'/members/')