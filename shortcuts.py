from django.template import loader
from django.http import HttpResponse, Http404
from django.template import RequestContext
from curia.authentication import check_access

def render_to_response(request, *args, **kwargs):
    return HttpResponse(loader.render_to_string(context_instance=RequestContext(request), *args, **kwargs))

def get_object_or_404_and_check_access(request, klass, **kwargs):
    from django.shortcuts import get_object_or_404
    command = None
    if 'command' in kwargs:
        command = kwargs['command']
        del kwargs['command']

    obj = get_object_or_404(klass, **kwargs)
    from curia import get_community_of
    if get_community_of(obj) != request.community:
        from curia.authentication import WrongCommunityException
        raise WrongCommunityException(obj)
    check_access(request.user, obj, level=2, command=command)
    return obj
   
def get_boolean(request,key,default=False):
    try:
        return request.REQUEST[key] == 'True'    
    except:
        return default
 
def get_integer(request,key,default=None):
    try:
        return int(request.REQUEST[key])
    except:
        return default
        
def get_string(request,key,default=None):
    try:
        return request.REQUEST[key]    
    except:
        return default