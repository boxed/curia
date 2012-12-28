import exceptions
from curia import get_objects_from, get_content_type, get_owner, get_community_of
from curia import get_current_community
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext as _
import datetime
from curia.authentication.cache import cache_access

class WrongCommunityException(exceptions.Exception):
    def __init__(self, obj):
        self.obj = obj
        self.args = {'obj':obj}

class AccessDeniedException(exceptions.Exception):
    user = None
    obj = None
    command = None

    def __init__(self, user, obj, command, comment = ''):
        self.user = user
        self.obj = obj
        self.command = command
        self.comment = comment
        self.args = {'user':user, 'obj':obj, 'command':command, 'comment':comment}

    #def __unicode__(self):
    #    return 'Access denied for command %s on object %s for user %s' % (self.user, self.obj, self.command)
    
def get_command(user, obj, command = None, level=1):
    if command == None:
        # guess command based on function name
        import inspect
        stackframe = inspect.stack()[level]
        function_name = stackframe[3]
        command = function_name.split('_')[0]

        # translate from function naming convention to django permission naming convention
        if command == 'edit':
            command = 'change'
        
        #if command not in ('change', 'delete', 'add', 'view', 'list'):
            #raise AccessDeniedException(user, obj, command, 'unknown access level')
            
    return command

def check_access(user, obj=None, command = None, level=1):
    command = get_command(user, obj, command, level+1)
    if command == 'edit':
        command = 'change'

    # check curia access level
    check_perm(user, obj, command)
    
class PermissionResponse:
    def __init__(self, granted, motivation):
        self.granted = granted
        self.motivation = motivation
        
    def __nonzero__(self):
        return self.granted
        
    def __unicode__(self):
        return smart_unicode(self.granted)+': '+unicode(self.motivation)
        
    def __repr__(self):
        return unicode(self)
        
def has_django_perm(user, obj, command):
    # translate from function naming convention to django permission naming convention
    if command == 'edit':
        command = 'change'

    if user.is_superuser:
        return PermissionResponse(True, 'user is superuser')
    
    if user.has_perm(obj._meta.app_label+'.can_'+command+'_'+obj._meta.module_name):
        return PermissionResponse(True, u'user has global permission on class')
    return None
    
@cache_access
def has_access_on_object(user, obj, content_type, command):
    # translate from function naming convention to django permission naming convention
    if command == 'edit':
        command = 'change'

    from curia.authentication.models import UserPermission
    user_permissions = get_objects_from(UserPermission, user=user, command=command, content_type=content_type, object_id=obj.id)
    if len(user_permissions) != 0:
        if user_permissions[0].deny:
            return PermissionResponse(False, u'user is denied permission on object')
        else:
            return PermissionResponse(True, u'user has permission on object')
    return None
    
@cache_access
def has_group_access_on_object(user, obj, content_type, command):
    from curia.authentication.models import GroupPermission
    for group in user.groups.exclude(name='everyone'):
        group_permissions = get_objects_from(GroupPermission, group=group, command=command, content_type=content_type, object_id=obj.id)
        if len(group_permissions) != 0:
            if group_permissions[0].deny:
                return PermissionResponse(False, u'user is a member of %s that is denied access to object' % group)
            else:
                return PermissionResponse(True, u'user is a member of %s with access to object' % group)
    return None
    
@cache_access
def has_access_on_content_type(user, content_type, command):
    from curia.authentication.models import UserPermission
    user_permissions = get_objects_from(UserPermission, user=user, command=command+' '+content_type.name, content_type=get_content_type(user), object_id=user.id)
    if len(user_permissions) != 0:
        if user_permissions[0].deny:
            return PermissionResponse(False, u'user is denied permissions on content type')
        else:
            return PermissionResponse(True, u'user has permissions on content type')
    return None
        
@cache_access
def has_group_access_on_content_type(user, content_type, command):
    if user == get_public_user():
        return None
    
    from curia.authentication.models import GroupPermission    
    for group in user.groups.exclude(name='everyone'):
        group_permissions = get_objects_from(GroupPermission, group=group, command=command+' '+content_type.name, content_type=get_content_type(user), object_id=user.id)
        if len(group_permissions) != 0:
            if user_permissions[0].deny:
                return PermissionResponse(False, u'user is a member of %s that is denied access to content type' % group)
            else:
                return PermissionResponse(True, u'user is a member of % with access to content type' % group)
    return None
    
@cache_access
def has_admin_access(user, obj, content_type, command):
    from curia.authentication.models import UserPermission
    try:
        community = get_current_community()
        permission = UserPermission.objects.get(user=user, object_id=community.id, content_type=get_content_type(community), command='administrate %s' % content_type)
        if permission.deny:
            return PermissionResponse(False, u'user is anti-admin for %s' % content_type)
        else:
            return PermissionResponse(True, u'user is admin for %s' % content_type)
    except UserPermission.DoesNotExist:
        return None
    
def has_perm(user, obj, command):
    owner = get_owner(obj)
    if owner == user:
        return PermissionResponse(True, 'user always has access on owned objects')

    from curia.authentication.models import GroupPermission 
    from django.contrib.auth.models import User, Group
    
    if get_community_of(obj).meta.created_by == user:
        return PermissionResponse(True, 'user is creator of current community')
    
    if command == 'add':
        if hasattr(obj, 'deleted') and obj.deleted:
            return PermissionResponse(True, 'add access is always denied on deleted objects')

    # translate from function naming convention to django permission naming convention
    if command == 'edit':
        command = 'change'
        
    if obj == None:
        obj = user
    
    if obj == user and command == 'view':
        return PermissionResponse(True, u'user can always view himself')
    
    if user.is_anonymous():
        return has_perm(get_public_user(), obj, command)
        
    if user != get_public_user():
        p = has_perm(user=get_public_user(), obj=obj, command=command)
        if p:
            return p
    
    response = has_django_perm(user, obj, command)
    if response is not None:
        return response
    
    content_type = get_content_type(obj)

    if user != get_public_user():
        response = has_admin_access(user, obj, content_type, command)
        if response is not None:
            return response

    response = has_access_on_object(user, obj, content_type, command)
    if response is not None:
        return response
    
    response = has_group_access_on_object(user, obj, content_type, command)
    if response is not None:
        return response
        
    # check content type level access
    everyone_permissions = get_objects_from(GroupPermission, group=get_everyone_group(), command=command, content_type=content_type, object_id=obj.id)
    if len(everyone_permissions) != 0:
        if everyone_permissions[0].deny:
            return PermissionResponse(False, u'everyone is denied access')
        else:
            return PermissionResponse(True, u'everyone is granted access')

    response = has_access_on_content_type(user, content_type, command)
    if response is not None:
        return response

    response = has_group_access_on_content_type(user, content_type, command)
    if response is not None:
        return response

    if owner != None:
        # check global access on the owner
        response = has_perm(user=user, obj=owner, command=command)
        # ignore access denied here, because we will check defaults and then return access denied later if need be
        if response:
            return response

    # default access levels
    if obj == user:
        return PermissionResponse(True, u'user has full access on self unless specifically denied')
        
    if command == 'view' or command == 'add':
        if isinstance(obj, Group):
            if user in obj.user_set.all():
                return PermissionResponse(True, 'everyone has view and add access by default in groups they are part of')

    community = get_current_community()
    if obj != community and get_community_of(obj) != community:
        raise WrongCommunityException(obj)
             
    if command == 'view' and isinstance(obj, User):
        if obj in community.user_set.all() and user in community.user_set.all():
            return PermissionResponse(True, u'everyone has view access on a user if they are in a community that the user in question is a member of')
  
    #if (command == 'change' or command == 'add') and isinstance(obj, Group):
    #    if obj.id in [group.id for group in user.groups.all()]:
    #        return PermissionResponse(True, 'members have change access by default on groups they are a member of')

    if hasattr(obj, 'has_default_permission'):
        response = obj.has_default_permission(user, command)
        if response is not None:
            return response
        
    if ' ' in command:
        return has_perm(user=user, obj=obj, command=command.split()[0])
        
    return PermissionResponse(False, u'%s has no %s permissions on %s' % (user, command, obj))
    
def check_perm(user, obj, command):
    foo = has_perm(user, obj, command)
    if not foo:
        raise AccessDeniedException(user, obj, command, foo.motivation)
    
def add_patterns(urlpatterns, cls):
    from django.conf import settings
    if 'curia.notifications' in settings.INSTALLED_APPS:
        from django.conf.urls.defaults import patterns
        urlpatterns += patterns('curia.authentication.views',
            (r'^(?P<object_id>\d+)/permissions/$', 'view_permissions', {'type': cls}),
            (r'^(?P<object_id>\d+)/permissions/advanced/$', 'view_advanced_permissions', {'type': cls}),
        )
    
def get_everyone_group():
    # TODO: add caching
    from django.contrib.auth.models import Group
    from curia.authentication.models import MetaGroup
    try:
        everyone = Group.objects.get(name='everyone')
    except Group.DoesNotExist:            
        everyone = Group(name='everyone')
        everyone.save()
        MetaGroup.objects.create(group=everyone, friend_group=True)
    return everyone
    
def get_public_user():
    # TODO: add caching
    from django.contrib.auth.models import User
    from curia.authentication.models import MetaUser
    try:
        public_user = User.objects.get(username='public_user')
    except User.DoesNotExist:
        public_user = User(username='public_user')
        public_user.save()
        MetaUser.objects.create(user=public_user)
    return public_user
    
def grant_access(command, obj, user=None, group=None):
    from curia.authentication.models import GroupPermission, UserPermission
    content_type = get_content_type(obj)
    if group != None:
        GroupPermission.objects.create(group=group, command=command, deny=False, content_type=content_type, object_id=obj.id)
    if user != None:
        UserPermission.objects.create(user=user, command=command, deny=False, content_type=content_type, object_id=obj.id)

def age(bday, d=datetime.date.today()):
    return (d.year - bday.year) - int((d.month, d.day) < (bday.month, bday.day))