from django.conf.urls.defaults import *

urlpatterns = patterns('curia.times.views',
    (r'^$', 'list_bookmarks'),
    (r'^(?P<time_id>\d+)/$', 'view_time'),
    (r'^(?P<time_id>\d+)/(?P<category>\w+)/$', 'view_category'),
    (r'^add/$', 'add_bookmark'),
    (r'^remove/$', 'remove_bookmark'),
)

