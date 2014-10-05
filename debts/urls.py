from django.conf.urls import *

urlpatterns = patterns('curia.debts.views',
    (r'^$', 'index'),
    (r'^(?P<transaction_id>\d+)/reject/$', 'reject_transaction'),
    (r'^log/$', 'view_log'),
    (r'^positive/$', 'view_positive_users'),
    (r'^negative/$', 'view_negative_users'),
    (r'^clear_rejected/$', 'clear_rejected'),
    
    (r'^api/list/$', 'api_list'),
    (r'^api/add/$', 'api_add'),
)