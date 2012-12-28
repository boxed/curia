from django.conf.urls.defaults import *
from curia.messages.models import Message
from curia import labels, authentication, notifications

urlpatterns = patterns('curia.messages.views',
    (r'^add/$', 'add_thread'),
    (r'^(?P<user_id>\d+)/$', 'view_messages'),
)

authentication.add_patterns(urlpatterns, Message)
notifications.add_patterns(urlpatterns, Message)