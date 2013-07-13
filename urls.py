from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^curia/', include('curia.foo.urls')),
    
    (r'^users/', include('curia.authentication.user_urls')),
    (r'^groups/', include('curia.authentication.group_urls')),
    
    (r'^login/', 'curia.authentication.views.login' ),
    (r'^logout/', 'curia.authentication.views.logout' ),

    (r'^forums/', include('curia.forums.urls') ),
    (r'^labels/', include('curia.labels.urls')),
    (r'^forums/', include('curia.forums.urls')),
    (r'^bookmarks/', include('curia.times.urls')),
    (r'^registration/', include('curia.registration.urls')),
    (r'^documents/', include('curia.documents.urls')),
    (r'^images/', include('curia.images.urls')),
    (r'^files/', include('curia.files.urls')),
    (r'^calendars/', include('curia.calendars.urls')),
    (r'^notifications/', include('curia.notifications.urls')),
    (r'^messages/', include('curia.messages.urls')),
    (r'^bugs/', include('curia.bugs.urls')),
    (r'^homepage/', include('curia.homepage.urls')),
    (r'^debts/', include('curia.debts.urls')),
)

urlpatterns += patterns('',
    (r'^$', 'curia.base.views.index'),
    (r'^administration/$', 'curia.base.views.administrate'),
    (r'^administration/delete/(?P<user_id>\d+)/$', 'curia.base.views.delete_administration_access'),
    (r'^external/$', 'curia.base.views.external'),
    (r'^search/$', 'curia.base.views.search'),
    (r'^contents/$', 'curia.base.views.contents'),
    (r'^navigation_ajax/$', 'curia.base.views.navigation_ajax'),
    (r'^notification_check/$', 'curia.base.views.notification_check'),
    (r'^portal/$', 'curia.base.views.portal'),
    (r'^members/$', 'curia.authentication.views.view_members'),
    #(r'^news/add/$', 'curia.base.views.add_news'),
    #(r'^news/edit/$', 'curia.base.views.edit_news'),
    #(r'^news/delete/$', 'curia.base.views.delete_news'),
    #(r'^news/archive/$', 'curia.base.views.view_news_archive'),
    (r'^create_community/$', 'curia.registration.views.create_community'),
    (r'^create_community/(?P<user_id>\d+)/$', 'curia.registration.views.create_community'),

    (r'^curia.css$', 'curia.base.views.stylesheet', {'template':'curia.css'}),
    (r'^community.css$', 'curia.base.views.stylesheet', {'template':'community.css'}),
    
    (r'^index.html$', 'curia.views.index_html'),
    
    (r'^autocomplete/(?P<key>.*)/$', 'curia.views.autocomplete'),

    (r'^members/$', 'curia.authentication.views.view_members'),
)

urlpatterns += patterns('',
    (r'^jsi18n/$', 'django.views.i18n.javascript_catalog', {'packages': 'django.conf'}),

    (r'^admin/', include(admin.site.urls)),
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
        
    # static content
    (r'^site-media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'C:/Python24/Lib/site-packages/django/contrib/admin/media'}),
)

urlpatterns += patterns('',
    (r'^echo_headers/$', 'curia.views.echo_headers'),
    (r'^test/$', 'curia.views.test'),
)
