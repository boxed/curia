from django.conf.urls.defaults import *

urlpatterns = patterns('curia.homepage.views',
    (r'^$', 'admin_index'),
    (r'^overview/$', 'overview'),
    (r'^menu/add/$', 'add_menu_item'),
)
