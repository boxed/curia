from django.contrib import admin
from curia.authentication.models import *

admin.site.register(MetaUser)
admin.site.register(MetaGroup)
admin.site.register(Detail)
admin.site.register(UserPermission)
admin.site.register(GroupPermission)
admin.site.register(Invite)