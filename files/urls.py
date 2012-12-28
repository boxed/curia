from django.conf.urls.defaults import *
from curia.files.models import File
from curia import labels, authentication, notifications

urlpatterns = patterns('curia.files.views',
    #(r'^users/(?P<user_id>\d+)/$', 'view_files_of_user'),
    (r'^add/$', 'add_file'),
    (r'^$', 'view_files_of_group'),
    (r'^page/(?P<page>\d+)/$', 'view_files_of_group'),
    (r'^groups/(?P<group_id>\d+)/$', 'view_files_of_group'),
    (r'^groups/(?P<group_id>\d+)/page/(?P<page>\d+)/$', 'view_files_of_group'),
    (r'^(?P<file_id>\d+)/edit/$', 'edit_file'),
    (r'^(?P<file_id>\d+)/delete/$', 'delete_file'),
)

authentication.add_patterns(urlpatterns, File)
notifications.add_patterns(urlpatterns, File, 'files/')
labels.add_patterns(urlpatterns, File)