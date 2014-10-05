from django.conf.urls import *
from django.contrib.auth.models import Group
from curia import labels, authentication, notifications

urlpatterns = patterns('curia.authentication.views',    
    (r'^add/$', 'add_group'),
    (r'^invite/$', 'reply_to_invitation'),
    (r'^edit/$', 'edit_group'),
    (r'^members/$', 'view_members'),
    (r'^members/page/(?P<page>\d+)/$', 'view_members'),
    (r'^uninvite/(?P<user_id>\d+)/$', 'remove_invitation_to_group'),
    (r'^(?P<group_id>\d+)/invite/$', 'reply_to_invitation'),
    (r'^(?P<group_id>\d+)/edit/$', 'edit_group'),
    (r'^(?P<group_id>\d+)/members/$', 'view_members'),
    (r'^(?P<group_id>\d+)/members/page/(?P<page>\d+)/$', 'view_members'),
    (r'^(?P<group_id>\d+)/uninvite/(?P<user_id>\d+)/$', 'remove_invitation_to_group'),

    #(r'^(?P<group_id>\d+)/$', 'view_group'),
    #(r'^(?P<name>\w+)/$', 'view_group_by_name'),
    #(r'^(?P<name>\w+)/contents/$', 'view_group_contents'),
    #(r'^(?P<group_id>\d+)/info/$', 'view_group_info'),
    #(r'^(?P<group_id>\d+)/toggle/$', 'toggle_group_activity'),
    #(r'^(?P<group_id>\d+)/delete/$', 'delete_group'),
    #(r'^(?P<group_id>\d+)/delete_member/(?P<user_id>\d+)/$', 'delete_member'),
    #(r'^(?P<group_id>\d+)/groups/$', 'view_groups_of_group'),
    #(r'^detail/(?P<detail_id>\d+)/delete/$', 'delete_detail'),
)

urlpatterns += patterns('curia.notifications.views',
    (r'^(?P<owner_group_id>\d+)/(?P<content_type>\w+)/watch/$', 'watch'),
    (r'^(?P<owner_group_id>\d+)/(?P<content_type>\w+)/ignore/$', 'ignore'),
)

authentication.add_patterns(urlpatterns, Group)
notifications.add_patterns(urlpatterns, Group)
