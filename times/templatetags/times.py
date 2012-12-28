from django.template import Library, TemplateSyntaxError, Node
from curia.times.models import Time
from curia.times import get_time_from, set_time_on, get_last_changed
from curia.authentication.templatetags.auth import get_item_from_context, resolve_parameter_from_context
from django.utils.encoding import smart_unicode

register = Library()

class UnreadNode(Node):
    def __init__(self, obj, obj2):
        self.obj = obj
        self.obj2 = obj2
        
    def render(self, context):
        obj = resolve_parameter_from_context(self.obj, context)
        user = resolve_parameter_from_context('user', context)
        try:
            obj2 = resolve_parameter_from_context(self.obj2, context)
            
            try:
                obj2time2 = context['time']
            except KeyError:
                obj2time2 = None
                
            obj2time = get_time_from(obj2, user).last_viewed
            
            try:
                objtime = obj.get_last_changed_for_user(user)
            except:
                objtime = obj.creation_time
    
            if obj2time is None or objtime is None:
                return ''
        
            if obj2time <= objtime:
                return ' unread'
            elif obj2time2 != None and obj2time2 <= objtime:
                return ' unread2'
            else:
                return ''
            #return smart_unicode(obj2time)+' '+unicode(objtime)+unicode(obj2time <= objtime)
        except KeyError:
            if get_last_changed(obj) > get_time_from(obj, user):
                return 'unread'
            else:
                return ''

def unread(parser, token):
    try:
        foo = token.contents.split(' ')
        obj = foo[1]
        obj2 = None
        if (len(foo) == 3):
            obj2 = foo[2]
    except ValueError:
        raise TemplateSyntaxError, "unread tag requires 1 or 2 arguments"
    return UnreadNode(obj, obj2)
        
class SetLastViewedNode(Node):
    def __init__(self, obj):
        self.obj = obj;
    
    def render(self, context):
        obj = get_item_from_context(self.obj, context)
        user = get_item_from_context('user', context)
        if not user.is_anonymous():
            set_time_on(obj, user)
        return ''

def set_last_viewed(parser, token):
    try:
        tag_name, obj = token.contents.split(' ')
    except ValueError:
        raise TemplateSyntaxError, "set_last_viewed tag requires an argument"
    return SetLastViewedNode(obj)


class IsBookmarkedNode(Node):
    def __init__(self, obj, nodelist_true, nodelist_false):
        self.obj = obj
        self.nodelist_true = nodelist_true
        self.nodelist_false = nodelist_false

    def render(self, context):
        obj = resolve_parameter_from_context(self.obj, context)
        user = resolve_parameter_from_context('user', context)

        if get_time_from(obj, user).bookmark:
            return self.nodelist_true.render(context)
        else:
            return self.nodelist_false.render(context)

def if_bookmarked(parser, token):
    try:
        tag_name, obj = token.contents.split(' ')
        nodelist_true = parser.parse(('else', 'endif_bookmarked'))
        token = parser.next_token()
        if token.contents == 'else':
            nodelist_false = parser.parse(('endif_bookmarked',))
            parser.delete_first_token()
        else:
            nodelist_false = NodeList()
        #nodelist = parser.parse(('endif_bookmarked',))
    except ValueError:
        raise TemplateSyntaxError, "if_bookmarked tag requires an argument"
    return IsBookmarkedNode(obj, nodelist_true, nodelist_false)

register.tag(unread)
register.tag(set_last_viewed)
register.tag(if_bookmarked)