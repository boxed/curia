from django.conf.urls.defaults import *
from curia.labels.models import Label
from curia import labels, authentication, notifications

urlpatterns = patterns('curia.labels.views',
    (r'^group/(?P<group_id>\d+)/delete/(?P<label_id>\d+)/$', 'delete_suggested_label'),
)
