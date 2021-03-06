from django.template import Library, TemplateSyntaxError, Node, TemplateDoesNotExist, resolve_variable, Context
from django.template.loader import get_template
from django.conf import settings
from django.template.defaultfilters import capfirst
from django.contrib.auth.models import Group
from curia.labels import get_labels
from django.template import NodeList
from curia.notifications import user_is_watching
from curia import split_and_honor_quotation_marks
from curia import get_content_type
from curia.context_processors import digg_paginator
from django.utils.translation import ugettext as _
from django.template.defaultfilters import stringfilter

register = Library()

register.filter('labels', get_labels)
register.inclusion_tag("digg_paginator.html", takes_context=True)(digg_paginator)

@register.filter
@stringfilter
def embed_data(value):
    import re
    links = list(re.finditer(r'(\[(.*?)\])', value)) # list() because we might need to reverse it later
    
    # examples of use:
    # [images/groups/1/sets/3]

    from django.core import urlresolvers
    from django.conf import settings

    links.reverse() # replace from the end as to not change the string in a way that interferes with the following replace operation
    for link in links:
        resolver = urlresolvers.RegexURLResolver(r'^/', settings.ROOT_URLCONF)
        callback, callback_args, callback_kwargs = resolver.resolve('/'+link.groups()[1]+'/')
        class Foo:
            pass
        request = Foo()
        from curia.authentication import get_public_user
        request.user = get_public_user()
        request.external = True
        request.community = None
        request.META = {'PATH_INFO':link.groups()[1]}
        request.domain = ''
        request.domain = ''
        request.mode = 'embed'
        request.GET = {}
        request.REQUEST = {}
        response = callback(request, *callback_args, **callback_kwargs)
        #replaced = get_content_for(link.groups()[1])
        # foo = dir(response)
        # bar = response.content
        value = value.replace(link.groups()[0], response.content)
            
    return value

@register.filter
def add_on_click_handler(value):
    import re
    p = re.compile(r'<a href=\"(.*?)\"')
    return p.sub(r'<a href="\1" class="g"', value)

@register.filter
def relative_date(value):
    from curia import relative_date_formatting
    return relative_date_formatting(value)

@register.filter
def spaces_to_underscore(value):
    return value.replace(' ', '_')

@register.filter
def javascript_string_escape(value):
    return value.replace('\r', '\n').replace('\\', '\\\\').replace('\n', '\\\n').replace('\"', '\\"')
    
@register.filter(name='contains')
def contains(value, arg):
    try:
        return arg in value
    except TypeError:
        return False

@register.filter(name='is_negative')
def is_negative(value):
    if float(value) < 0:
        return True
    else:
        return False

@register.filter(name='content_type')
def content_type(value):
    return get_content_type(value)

@register.filter(name='dir')
def dir_filter(value):
    return dir(value)

@register.filter
def multiply(value, arg):
    return float(value) * float(arg)

@register.filter
def absolute(value):
    return abs(value)

@register.filter
def divide(value, arg):
    return float(value) / float(arg)

@register.filter
def subtract(value, arg):
    return float(value) - float(arg)

@register.filter
def power(value, arg):
    return float(value) ** float(arg)

def replace_spaces(value):
    result = ''
    for character in value.group():
        if character == '\t':
            result += '&nbsp;&nbsp;&nbsp;'
        elif character == ' ':
            result += '&nbsp;'
        else:
            result += '\n'
        
    return result
    
@register.filter
def linebreaks_and_spaces(value):
    import re
    value = value.replace('\n\n', '<p></p>\n')
    value = re.sub('([^>])\n', '\g<1><br />\n', value)
    pattern = re.compile(r'\n[ \t]+')
    from curia.feedparser import _sanitizeHTML
    from django.template.defaultfilters import safe
    return safe(pattern.sub(replace_spaces, _sanitizeHTML(value, settings.DEFAULT_CHARSET)))

@register.filter
def sanitize(value):
    from curia.feedparser import _sanitizeHTML
    from django.template.defaultfilters import safe
    return safe(_sanitizeHTML(value, settings.DEFAULT_CHARSET))

@register.filter(name='truncateletters')
def truncateletters(value, arg):
    """
    Truncates a string after a certain number of letters

    Argument: Number of letters to truncate after
    """
    def truncate_letters(s, num):
        """Truncates a string after a certain number of letters."""
        length = int(num)
        letters = [l for l in s]
        if len(letters) > length:
            letters = letters[:length]
            if not letters[-3:] == ['.','.','.']:
                letters += ['.','.','.']
        return ''.join(letters)

    try:
        length = int(arg)
    except ValueError: # invalid literal for int()
        return value # Fail silently
    if not isinstance(value, basestring):
        value = str(value)
    return truncate_letters(value, length)

def is_string_literal(s):
    return s[0] in ('"', "'") and  s[-1] == s[0]

def get_item_from_context(item, context):
    path = item.split('.')
    result = context.__getitem__(path[0])
    for i in path[1:]:
        result = getattr(result, i)
        if callable(result):
            result = result()
    return result
    
def resolve_parameter_from_context(source_name, context):
    if source_name is None:
        raise KeyError('no key specified')
    if is_string_literal(source_name):
        return source_name[1:-1]
    else:
        return get_item_from_context(source_name, context)
    
def resolve_parameters_from_context(parameters, context):
    new_context = {}
    for parameter in parameters:
        destination_name, source_name = parameter.split('=')
        new_context[destination_name] = resolve_parameter_from_context(source_name, context)
    return new_context

class IncludeNode(Node):
    def __init__(self, template_name, parameters):
        self.template_name = template_name
        self.parameters = parameters

    def render(self, context):
        try:
            if is_string_literal(self.template_name):
                template_name = resolve_variable(self.template_name, context)
            else:
                template_name = self.template_name
            t = get_template(template_name)
        
            # add parameters to context
            new_context = resolve_parameters_from_context(self.parameters, context)
            context.update(new_context)
            result = t.render(Context(context))
            context.pop()
            return result
            
        except TemplateSyntaxError:
            if settings.TEMPLATE_DEBUG:
                raise
            return ''

@register.tag
def curia_include(parser, token):
    """
    Loads a template and renders it with the current context. Passes any named parameters that are in the form of "a=b".

    Example::

        {% include "foo/some_include" object=user %}
    """
    del parser
    bits = split_and_honor_quotation_marks(token.contents)
    if len(bits) < 2:
        raise TemplateSyntaxError, "%r tag takes one argument: the name of the template to be included" % bits[0]
    
    return IncludeNode(bits[1], bits[2:])

def make_keys_str(params):
    result = {}
    for key in params:
        result[str(key)] = params[key]
    return result

class WatcherLinkNode(Node):
    def __init__(self, parameters):
        self.parameters = parameters

    def render(self, context):
        try:
            parameters = resolve_parameters_from_context(self.parameters, context)
            obj = None
            if 'owner' in parameters:
                obj = parameters['owner']
            if 'obj' in parameters:
                obj = parameters['obj']

            if callable(obj):
                obj = obj()
                
            url = obj.get_absolute_url()
            if 'content_type' in parameters:
                if isinstance(parameters['content_type'], unicode):
                    url += parameters['content_type']+'/'
                else:
                    url += parameters['content_type'].name+'/'
            
            result = ''
            
            try:
                if user_is_watching(user=context['user'], **make_keys_str(parameters)):
                    result += '<a class="button" href="'+url+'ignore/">'+_('Stop watching')+'</a>'
                else:          
                    result += '<a class="button" href="'+url+'watch/">'+_('Watch')+'</a>'
            except:
                return ''
            
            return result

        except TemplateSyntaxError:
            if settings.TEMPLATE_DEBUG:
                raise
            return ''

@register.tag
def watcher_link(parser, token):
    """
    Renders a watch or ignore link for the specified context.

    Example::

        {% watcher_link owner=user content_type="document" %}
    """
    del parser
    bits = split_and_honor_quotation_marks(token.contents)
    if len(bits) < 2:
        raise TemplateSyntaxError, "%r tag at least one argument" % bits[0]
    
    return WatcherLinkNode(bits[1:])

class BasePermissionNode(Node):
    def __init__(self, parameters):
        self.parameters = parameters

    def render(self, context):
        try:
            parameters = resolve_parameters_from_context(self.parameters, context)
                
            obj = None
            if 'obj' in parameters:
                obj = parameters['obj']

            if obj is None:
                obj = context['user']

            if callable(obj):
                obj = obj()

            url = obj.get_absolute_url()

            command = 'view'
            if 'command' in parameters:
                command = parameters['command']

            css_command = command
            if css_command == 'edit':
                css_command = 'change'

            if 'title' in parameters:
                title = _(parameters['title'])
            elif command == 'view':
                title = _(capfirst(unicode(obj)))
            else:
                title = _(capfirst(command))

            if command != 'view':
                url += command+'/' 

            if 'add ' in command:
                foo = command.split(' ')
                if foo[1] == 'member':
                    url = '/groups/'+unicode(obj.id)+'/add_member/'
                elif foo[1] == 'friend':
                    url = '/users/'+unicode(obj.id)+'/add_friend/'
                else:    
                    url = '/'+foo[1]+'s/add/'
                    if isinstance(obj, Group):
                        url += '?group_id='+unicode(obj.id)
                    else:
                        url += '?user_id='+unicode(obj.id)
            from curia.authentication import has_perm
            
            perm = has_perm(user=context['user'], obj=obj, command=command)
            
            if perm:
                return self.has_permission(context, url, css_command, title, perm.motivation)
            else:
                return self.no_permission(context, url, css_command, title, perm.motivation)

        except TemplateSyntaxError:
            if settings.TEMPLATE_DEBUG:
                raise
            return ''
    

class LinkNode(BasePermissionNode):
    def has_permission(self, context, url, css_command, title, motivation):
        del context
        if css_command == 'view':
            return '<a href="'+url+'">'+title+'</a>'
        
        title = capfirst(unicode(title))
        from django.conf import settings
        return '<a href="%s" title="%s"><img src="%scommands/%s.png" alt="%s" /></a><!-- %s -->' % (url, title, settings.MEDIA_URL, css_command.split(' ')[0], title, motivation)
    
    def no_permission(self, context, url, css_command, title, motivation):
        del context, url, css_command, title
        return '<!-- '+motivation+'-->'

@register.tag
def link(parser, token):
    """
    Renders a link for the specified object and command.
    Available commands are "edit", "delete" and "view", the default command is "view".

    Example::

        {% link obj=document command="edit" %}
    """
    del parser
    bits = split_and_honor_quotation_marks(token.contents)
    if len(bits) < 2:
        raise TemplateSyntaxError, "%r tag at least one argument" % bits[0]
    
    return LinkNode(bits[1:])

class HasPermissionNode(BasePermissionNode):
    def __init__(self, parameters, nodelist_true, nodelist_false):
        super(HasPermissionNode, self).__init__(parameters)
        self.parameters = parameters
        self.nodelist_false = nodelist_false
        self.nodelist_true = nodelist_true
    
    def has_permission(self, context, url, css_command, title, motivation):
        del url, css_command, title
        return '<!-- '+motivation+'-->' + self.nodelist_true.render(context)
    
    def no_permission(self, context, url, css_command, title, motivation):
        del url, css_command, title
        return '<!-- '+motivation+'-->' + self.nodelist_false.render(context)
    
@register.tag
def has_permission(parser, token):
    """
    Renders the body if the user has the specified access on the given object.
    Available commands are "edit", "delete" and "view", the default command is "view".

    Example::

        {% has_permission obj=document command="edit" %}you have access!{% endhas_permission %}
    """
    bits = split_and_honor_quotation_marks(token.contents)
    
    nodelist_true = parser.parse(('else', 'endhas_permission'))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse(('endhas_permission',))
        parser.delete_first_token()
    else:
        nodelist_false = NodeList()
    
    if len(bits) < 2:
        raise TemplateSyntaxError, "%r tag at least one argument" % bits[0]

    return HasPermissionNode(bits[1:], nodelist_true, nodelist_false)
    
