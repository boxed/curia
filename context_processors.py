from django.contrib.sites.models import Site
from django.utils.translation import ugettext as _
from curia.shortcuts import get_string

def site(request):
    return {'site': Site.objects.get_current()}

class LazyLoadGroups:
    def __init__(self, request):
        self._request = request
        self._groups = None
        self._groups_of_user = None
    
    def all(self):
        if self._groups == None:
            self._groups = []
            for group in self._request.user.groups.all():
                if group.meta.deleted == False and group.meta.friend_group == False:
                    self._groups.append(group)
        return self._groups
    
    def in_community(self):
        if self._groups_of_user == None:
            from curia.authentication.models import MetaGroup
            community_groups = [self._request.community.meta]
            for g in self._request.community.meta.children.all():
                if g.deleted == False:
                    community_groups.append(g)
            community_groups = set([g.group.id for g in community_groups])
            self._groups_of_user = []
            for group in self.all():
                if group.id in community_groups:
                    self._groups_of_user.append(group)
        return self._groups_of_user
    
def external(request):
    from curia.notifications.models import Notification, Bookmark
    from curia.calendars.models import Reply
    from curia.authentication.models import Invite
    from django.conf import settings

    if 'HTTP_USER_AGENT' in request.META:
        user_agent = request.META['HTTP_USER_AGENT'].lower()
    else:
        user_agent = 'unknown'

    request.external_theme = 'default'
    request.internal_theme = 'default'
    if request.community != None and request.community.meta.internal_theme != '':
        request.internal_theme = request.community.meta.internal_theme
    if request.community != None and request.community.meta.external_theme != '':
        request.external_theme = request.community.meta.external_theme
    
    if request.external:
        base = 'themes/%s/external_with_homepage.html' % request.external_theme # external.html
        #if unicode(request.community).lower() == u'fest':
        #    base = 'homepage/templates/saldo.html' # external.html
        if request.mode == 'embed':
            base = 'embed.html'
        
        from curia.homepage.models import MenuItem
        menu = MenuItem.objects.filter(group=request.community, parent__isnull=True)
        try:
            current_menu_location = MenuItem.objects.get(group=request.community, url=request.META['PATH_INFO'])
            if current_menu_location.parent != None:
                submenu = MenuItem.objects.filter(group=request.community, parent=current_menu_location.parent)
                current_submenu_location = current_menu_location
                current_menu_location = current_submenu_location.parent
            else:
                submenu = MenuItem.objects.filter(group=request.community, parent=current_menu_location)
        except MenuItem.DoesNotExist:
            current_menu_location = None
            submenu = None
        if len(menu) == 0:
            base = 'themes/%s/external_without_homepage.html' % request.external_theme

        is_member = False
        if request.community and request.user in request.community.user_set.all() or request.user.is_superuser:
            is_member = True
    
        from curia.authentication.views import LoginForm
        return {
            'external':True, 
            'community':request.community, 
            'is_member':is_member,
            'domain':request.domain, 
            'login_address':'http://%s/login/'% request.domain, 
            'menu':menu, 
            'current_menu_location':current_menu_location, 
            'submenu':submenu, 
            'base':base,  
            'edit_base':'themes/default/external_without_homepage_edit.html', 
            'login_form':LoginForm(initial={}),
            'user_agent':user_agent,
            'settings':settings,
            }
    
    if 'current_url' in request.REQUEST:
        current_url = request.REQUEST['current_url']
    else:
        current_url = request.get_full_path()

    return {
        'method':request.method,
        'current_url':current_url,
        'external': False, 
        'community':request.community, 
        'domain':request.domain, 
        'base':'themes/%s/internal.html' % request.internal_theme,  
        'edit_base':'themes/%s/internal.html' % request.internal_theme,
        'groups_of_user':LazyLoadGroups(request),
        'user_agent':user_agent,
        'settings':settings,
        }
    
def domain(request):
    return {'domain':request.domain, 'port':request.port, 'is_homepage_admin':request.mode == 'admin', 'is_homepage':request.mode == 'homepage'}
    
LEADING_PAGE_RANGE_DISPLAYED = TRAILING_PAGE_RANGE_DISPLAYED = 10
LEADING_PAGE_RANGE = TRAILING_PAGE_RANGE = 8
NUM_PAGES_OUTSIDE_RANGE = 2 
ADJACENT_PAGES = 4

def digg_paginator(context):
    try:
        context["search"]
    except:
        context["search"] = None
    if 'paginator' in context:
        " Initialize variables "
        in_leading_range = in_trailing_range = False
        pages_outside_leading_range = pages_outside_trailing_range = range(0)
        
        paginator = context['paginator']
        page = int(context['page'])
        
        number_of_pages = context['number_of_pages'] if 'number_of_pages' in context else paginator.num_pages
        page_size = context['page_size'] if 'page_size' in context else paginator.per_page

        if number_of_pages <= LEADING_PAGE_RANGE_DISPLAYED:
            in_leading_range = in_trailing_range = True
            page_numbers = [n for n in range(1, number_of_pages + 1) if n > 0 and n <= number_of_pages]           
        elif context["page"] <= LEADING_PAGE_RANGE:
            in_leading_range = True
            page_numbers = [n for n in range(1, LEADING_PAGE_RANGE_DISPLAYED + 1) if n > 0 and n <= number_of_pages]
            pages_outside_leading_range = [n + number_of_pages for n in range(0, -NUM_PAGES_OUTSIDE_RANGE, -1)]
        elif context["page"] > number_of_pages - TRAILING_PAGE_RANGE:
            in_trailing_range = True
            page_numbers = [n for n in range(number_of_pages - TRAILING_PAGE_RANGE_DISPLAYED + 1, number_of_pages + 1) if n > 0 and n <= number_of_pages]
            pages_outside_trailing_range = [n + 1 for n in range(0, NUM_PAGES_OUTSIDE_RANGE)]
        else: 
            page_numbers = [n for n in range(context["page"] - ADJACENT_PAGES, context["page"] + ADJACENT_PAGES + 1) if n > 0 and n <= number_of_pages]
            pages_outside_leading_range = [n + number_of_pages for n in range(0, -NUM_PAGES_OUTSIDE_RANGE, -1)]
            pages_outside_trailing_range = [n + 1 for n in range(0, NUM_PAGES_OUTSIDE_RANGE)]
        return {
            "base_url": context["base_url"],
            "is_paginated": True,
            "previous_page": page-1,
            "has_previous_page": paginator.page(page).has_previous(),
            "next_page": page+1,
            "has_next_page": paginator.page(page).has_next(),
            "page_size": page_size,
            "page": page,
            "number_of_pages": paginator.num_pages,
            "page_numbers": page_numbers,
            "in_leading_range" : in_leading_range,
            "in_trailing_range" : in_trailing_range,
            "pages_outside_leading_range": pages_outside_leading_range,
            "pages_outside_trailing_range": pages_outside_trailing_range,
            "search": context["search"]
        }