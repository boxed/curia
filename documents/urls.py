from django.conf.urls.defaults import *
from curia.documents.models import Document
from curia import labels, authentication, notifications

urlpatterns = patterns('curia.documents.views',
    (r'^add/$', 'add_document'),
    (r'^/$', 'view_documents_of_group'),
    (r'^groups/(?P<group_id>\d+)/$', 'view_documents_of_group'),
    (r'^users/(?P<user_id>\d+)/$', 'view_documents_of_user'),
    (r'^(?P<document_id>\d+)/$', 'view_latest'),
    (r'^(?P<document_id>\d+)/edit/$', 'edit_document'),
    (r'^(?P<document_id>\d+)/delete/$', 'delete_document'),
    (r'^(?P<document_id>\d+)/versions/$', 'view_version_list'),
    (r'^(?P<document_id>\d+)/version/(?P<version_id>\d+)/$', 'view_version'),
    (r'^(?P<document_id>\d+)/version/(?P<version_id>\d+)/revert/$', 'revert_to_version'),
)

authentication.add_patterns(urlpatterns, Document)
notifications.add_patterns(urlpatterns, Document)