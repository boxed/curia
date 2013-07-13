from django.conf.urls.defaults import *
from django.conf import settings

try:
    registration_system = settings.REGISTRATION_SYSTEM
except:
    registration_system = 'invite'

urlpatterns = patterns('curia.registration.views',
    (r'^email_sent/$', 'email_sent'),
    #(r'^new_community/$', 'new_community'),
    (r'^set_new_password/$', 'set_new_password'),
    (r'^request_new_password/$', 'request_new_password'),
)

if registration_system == 'invite':
    urlpatterns += patterns('curia.registration.views',
        (r'^$', 'invite'),
        (r'^accept/$', 'accept'),
        (r'^invite/(?P<invite_id>\d+)/delete/$', 'delete_invite'),
    )
elif registration_system == 'register':
    urlpatterns += patterns('curia.registration.views',
        (r'^$', 'register'),
        (r'^complete/$', 'accept'),
    )

urlpatterns += patterns('django.views.generic.simple',
    # (r'^administrator_agreement/$', 'direct_to_template', {'template': 'registration/administrator_agreement.html'}),
    # (r'^user_agreement/$', 'direct_to_template', {'template': 'registration/user_agreement.html'}),
)
