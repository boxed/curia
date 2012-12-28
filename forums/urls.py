from django.conf.urls.defaults import *
from curia.forums.models import Thread
from curia import labels, authentication, notifications

urlpatterns = patterns('curia.forums.views',
    (r'^$', 'view_forum'),
    (r'^add/$', 'add_thread'),
    (r'^page/(?P<page>\d+)/$', 'view_forum'),
    (r'^(?P<group_id>\d+)/$', 'view_forum'),
    (r'^(?P<group_id>\d+)/add/$', 'add_thread'),
    (r'^(?P<group_id>\d+)/page/(?P<page>\d+)/$', 'view_forum'),
    (r'^threads/(?P<thread_id>\d+)/$', 'view_thread'),
    (r'^threads/(?P<thread_id>\d+)/page/(?P<page>\d+)/$', 'view_thread'),
    (r'^threads/(?P<thread_id>\d+)/edit/$', 'edit_thread'),
    (r'^threads/(?P<thread_id>\d+)/delete/$', 'delete_thread'),
    (r'^message/(?P<message_id>\d+)/delete/$', 'delete_message'),
    (r'^message/(?P<message_id>\d+)/edit/$', 'edit_message'),
)

authentication.add_patterns(urlpatterns, Thread)
notifications.add_patterns(urlpatterns, Thread, 'threads/')
labels.add_patterns(urlpatterns, Thread)