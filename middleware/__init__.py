###
# Copyright (c) 2006-2007, Jared Kuolt
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the SuperJared.com nor the names of its
#       contributors may be used to endorse or promote products derived from
#       this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
###

from django.conf import settings
from django.contrib.auth.views import login
from django.http import HttpResponseRedirect, HttpResponse
from django.utils.translation import ugettext as _

#class ErrorMiddleware(object):
#    def process_exception(self, request, exception):
#        from curia.authentication import AccessDeniedException
#        if isinstance(exception, AccessDeniedException):
#            return HttpResponse(_('Access denied'))
#        return None

class RequireLoginMiddleware(object):
    """
    Require Login middleware. If enabled, each Django-powered page will
    require authentication.
   
    If an anonymous user requests a page, he/she is redirected to the login
    page set by REQUIRE_LOGIN_PATH or /accounts/login/ by default.
    """
    def __init__(self):
            self.require_login_path = getattr(settings, 'REQUIRE_LOGIN_PATH', '/login/')

    def process_exception(self, request, exception):
        from curia.authentication import AccessDeniedException, WrongCommunityException
        from curia.shortcuts import render_to_response
        if isinstance(exception, AccessDeniedException):
            if request.user.is_anonymous():
                return HttpResponseRedirect('%s?next=%s' % (self.require_login_path, request.path))
            
            from django.http import HttpResponseForbidden
            from django.template import loader
            from django.template import RequestContext
            return HttpResponseForbidden(loader.render_to_string(context_instance=RequestContext(request), dictionary={'comment': exception.comment}, template_name='403.html'), status=403)
        elif isinstance(exception, WrongCommunityException):
            from curia import get_community_of
            obj = exception.obj
            obj_community = get_community_of(obj)
            from django.conf import settings
            domain = 'http://%s' % obj_community.meta.domain
            port_marker = request.META['HTTP_HOST'].rfind(':', 5)
            if port_marker != -1:
                domain += request.META['HTTP_HOST'][port_marker:]
            
            if request.META['QUERY_STRING'] == None:
                path = '%s%s' % (domain, request.path)
            else:
                path = '%s%s?%s' % (domain, request.path, request.META['QUERY_STRING'])
            return HttpResponseRedirect(path)
        return None                

#### end of copyright notice

class CuriaMiddleware(object):
    def __init__(self):
        self.require_login_path = getattr(settings, 'REQUIRE_LOGIN_PATH', '/login/')
        
    def process_response(self, request, response):
        from django.contrib.flatpages.views import flatpage
        from django.http import Http404
        from django.conf import settings
        if response.status_code != 404:
            return response # No need to check for a flatpage for non-404 responses.
        try:
            path = request.path
            if path[-1:] != '/':
                path += '/'
            return flatpage(request, path)
        # Return the original response if any errors happened. Because this
        # is a middleware, we can't assume the errors will be caught elsewhere.
        except Http404:
            return response
        except:
            if settings.DEBUG:
                raise
            return response

    def process_request(self, request):
        host = request.META['HTTP_HOST']
        if host.startswith('www.'):
            return HttpResponseRedirect('http://%s%s' % (request.META['HTTP_HOST'][4:], request.path))
                
        first_domain_part = host[0:host.find('.')]
        request.external = True
        if first_domain_part == 'admin':
            request.domain = host[host.find('.')+1:]
            request.mode = 'admin'
        elif first_domain_part == 'community':
            request.external = False
            request.domain = host[host.find('.')+1:]
            request.mode = 'community'
            if not request.user.is_authenticated() and 'navigation_ajax' not in request.path:
                return HttpResponseRedirect('http://%s%s?next=http://community.%s%s' % (request.domain, self.require_login_path, request.domain, request.path))
        else:
            request.domain = host
            request.mode = 'homepage'

        from curia.authentication.models import MetaGroup
        try:
            domain = request.domain
            request.port = ''
            port_marker = domain.rfind(':', 5)
            if port_marker != -1:
                request.port = domain[port_marker:]
                domain = domain[0:port_marker]
            if domain.endswith('eldmyra.net'):
                domain = domain[:-3]+'se'
            request.community = MetaGroup.objects.get(domain__iexact=domain).group
        except MetaGroup.DoesNotExist:
            request.community = None
            
        # threadlocals middleware
        from curia import _thread_locals
        _thread_locals.request = request
        _thread_locals.user = request.user
        _thread_locals.community = request.community
        
        request.access_cache = {}
        
        if 'django_language' not in request.session:
            from locale import setlocale, LC_ALL, getlocale
            #setlocale(LC_ALL, settings.LANGUAGE_CODE.replace('-', '_'))
            request.session['django_language'] = settings.LANGUAGE_CODE
