from django.conf.urls import *
from django.conf import settings
from curia import labels, authentication, notifications
from curia.calendars.models import Event

urlpatterns = patterns('curia.calendars.views',
    (r'^events/(?P<event_id>\d+)/$', 'view_event'),
    (r'^events/(?P<event_id>\d+)/edit/$', 'edit_event'),
    (r'^events/(?P<event_id>\d+)/delete/$', 'delete_event'),
    (r'^events/(?P<event_id>\d+)/reply/$', 'reply_to_event'),
    (r'^events/(?P<event_id>\d+)/reply/(?P<new_reply>\w+)/$', 'reply'),
    (r'^events/(?P<event_id>\d+)/view/$', 'show_replies_of_event'),
    (r'^groups/(?P<group_id>\d+)/add/$', 'add_event_to_group'),
    (r'^add/$', 'add_event_to_group'),
    (r'^$', 'view_group'),
    (r'^agenda/$', 'view_agenda_of_group'),
    (r'^(?P<year>\d+)/(?P<month>\d+)/$', 'view_month_for_group'),
    (r'^groups/(?P<group_id>\d+)/$', 'view_group'),
    (r'^groups/(?P<group_id>\d+)/agenda/$', 'view_agenda_of_group'),
    (r'^groups/(?P<group_id>\d+)/(?P<year>\d+)/(?P<month>\d+)/$', 'view_month_for_group'),
    #(r'^users/(?P<user_id>\d+)/add/$', 'add_event_to_user'),
    #(r'^users/(?P<user_id>\d+)/$', 'view_user'),
    #(r'^users/(?P<user_id>\d+)/agenda/$', 'view_agenda_of_user'),
    #(r'^users/(?P<user_id>\d+)/(?P<year>\d+)/(?P<month>\d+)/$', 'view_month_for_user'),
)

authentication.add_patterns(urlpatterns, Event)
notifications.add_patterns(urlpatterns, Event)
