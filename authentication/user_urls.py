from django.conf.urls.defaults import *
from django.contrib.auth.models import User
from curia import labels, authentication, notifications, base

urlpatterns = patterns('curia.authentication.views',
    # Example:
    # (r'^curia/', include('curia.foo.urls')),

    (r'^(?P<user_id>\d+)/$', 'view_user'),
    #(r'^(?P<user_id>\d+)/info/$', 'view_user_info'),
    #(r'^(?P<name>\w+)/$', 'view_user_by_name'),
    #(r'^(?P<name>\w+)/contents/$', 'view_user_contents'),
    (r'^(?P<user_id>\d+)/edit/$', 'edit_user'),
    (r'^(?P<user_id>\d+)/settings/$', 'edit_user_settings'),
    (r'^(?P<user_id>\d+)/settings/password/$', 'edit_user_password'),
    #(r'^(?P<user_id>\d+)/delete/$', 'delete_user'),
    #(r'^(?P<user_id>\d+)/friends/$', 'view_friends'),
    (r'^(?P<user_id>\d+)/friends/uninvite/(?P<invited_id>\d+)/$', 'remove_invitation'),
    #(r'^(?P<user_id>\d+)/groups/$', 'view_groups_of_user'),
    #(r'^(?P<user_id>\d+)/delete_friend/(?P<friend_id>\d+)/$', 'delete_friend'),
    #(r'^detail/(?P<detail_id>\d+)/delete/$', 'delete_detail'),
    (r'^permission/(?P<permission_id>\d+)/delete/$', 'delete_permission'),
)

urlpatterns += patterns('curia.notifications.views',
    (r'^(?P<owner_user_id>\d+)/(?P<content_type>\w+)/watch/$', 'watch'),
    (r'^(?P<owner_user_id>\d+)/(?P<content_type>\w+)/ignore/$', 'ignore'),
)

urlpatterns += patterns('curia.registration.views',
    (r'^(?P<user_id>\d+)/invite/$', 'invite'),
)

authentication.add_patterns(urlpatterns, User)
notifications.add_patterns(urlpatterns, User)
