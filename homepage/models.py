from django.db import models
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

class MenuItem(models.Model):
    group = models.ForeignKey(Group, name=_('Group'))
    parent = models.ForeignKey('self', blank=True, null=True, related_name='child_menus')
    order = models.IntegerField(name=_('Order'))
    content_type = models.ForeignKey(ContentType, name=_('Content type'))
    object_id = models.IntegerField(_('Object ID'), name=_('Object ID'))
    title = models.CharField(max_length=1024, name=_('Name'))
    url = models.CharField(max_length=1024, name=_('Url'))
    
    def __unicode__(self):
        return '<li id="id_%s"><a href="%s">%s</a></li>' % (self.title, self.url, self.title,)
    
    class Admin:
        pass
        
    class Meta:
        ordering = ['order']
        verbose_name = _('menu item')
        verbose_name_plural = _('menu items')
        #unique_together = (('group', 'content_type', 'object_id'))
