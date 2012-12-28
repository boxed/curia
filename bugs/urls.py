from django.conf.urls.defaults import *
from curia.forums.models import Thread
from curia import labels, authentication, notifications

urlpatterns = patterns('curia.bugs.views',
    (r'^report/$', 'report_bug'),
    #(r'^/$', 'list_bugs'),
)