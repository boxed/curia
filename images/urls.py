from django.conf.urls.defaults import *
from curia.images.models import Image
from curia import labels, authentication, notifications

urlpatterns = patterns('curia.images.views',
    #(r'^$', ''),
    #(r'^users/(?P<user_id>\d+)/$', 'view_images_of_user'),
    #(r'^users/(?P<user_id>\d+)/sets/$', 'view_sets_of_user'),
    #(r'^groups/(?P<group_id>\d+)/$', 'view_images_of_group'),
    (r'^groups/(?P<group_id>\d+)/sets/$', 'view_sets_of_group'),
    (r'^groups/(?P<group_id>\d+)/sets/page/(?P<page>\d+)/$', 'view_sets_of_group'),
    (r'^groups/(?P<group_id>\d+)/sets/(?P<set_id>\d+)/edit/$', 'edit_set'),
    (r'^groups/(?P<group_id>\d+)/sets/add/$', 'add_set'),
    (r'^sets/$', 'view_sets_of_group'),
    (r'^sets/page/(?P<page>\d+)/$', 'view_sets_of_group'),
    (r'^sets/(?P<set_id>\d+)/edit/$', 'edit_set'),
    (r'^sets/add/$', 'add_set'),
    (r'^sets/(?P<set_id>\d+)/$', 'view_set'),
    (r'^sets/(?P<set_id>\d+)/page/(?P<page>\d+)/$', 'view_set'),
    (r'^sets/(?P<set_id>\d+)/add/$', 'add_image'),
    #(r'^sets/(?P<set_id>\d+)/mass_edit/$', 'mass_edit_images'),
    (r'^sets/(?P<set_id>\d+)/delete/$', 'delete_image_set'),
    (r'^sets/(?P<set_id>\d+)/representative/(?P<image_id>\d+)/$', 'edit_representative_image'),
    (r'^(?P<image_id>\d+)/$', 'view_image'),
    (r'^(?P<image_id>\d+)/edit/$', 'edit_image'),
    (r'^(?P<image_id>\d+)/delete/$', 'delete_image'),
)

authentication.add_patterns(urlpatterns, Image)
notifications.add_patterns(urlpatterns, Image)