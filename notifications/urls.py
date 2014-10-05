from django.conf.urls import *

urlpatterns = patterns('curia.notifications.views',
    (r'^(?P<notification_id>\d+)/delete/$', 'delete_notification'),    
    (r'^watchers/$', 'view_watchers'),
    (r'^watchers/(?P<watcher_id>\d+)/delete/$', 'delete_watcher'),
    (r'^bookmarks/$', 'view_bookmarks'),
    (r'^bookmarks/delete/$', 'delete_bookmark'),
    (r'^bookmarks/add/$', 'add_bookmark'),
    (r'^bookmarks/(?P<bookmark_id>\d+)/delete/$', 'delete_bookmark'),
    (r'^new/(?P<content_type_id>\d+)/$', 'view_new_objects'),
    (r'^new/(?P<content_type_id>\d+)/delete/$', 'delete_new_objects_of_type'),
)