from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models import signals
from django.dispatch import dispatcher
from django.utils.translation import ugettext_lazy as _
from curia.notifications import notify
from django.utils.encoding import smart_unicode

class Document(models.Model):
    owner_user = models.ForeignKey(User, blank=True, null=True, verbose_name=_('Owner user'), name=_('owner user'))
    owner_group = models.ForeignKey(Group, blank=True, null=True, verbose_name=_('Owner group'), name=_('owner group'))
    creation_time = models.DateTimeField(auto_now_add=True, name=_('Creation time'))
    is_presentation = models.BooleanField(default=False, name=_('Is presentation'))
    deleted = models.BooleanField(default=False, name=_('Deleted'))
    deleted_by = models.ForeignKey(User, blank=True, null=True, default=None, related_name="deleted_documents", name=_('Deleted by'))
    deletion_time = models.DateTimeField(blank=True, null=True, name=_('Deletion time'))
    title = models.CharField(max_length=1024,blank=True, default='<Document without version>')
    
    def get_latest_version(self):
        try:
            return Version.objects.filter(document=self.id).order_by('-creation_time')[0]
        except IndexError:
            return None
         
    def save(self, force_insert=False, using=None):
        if self.owner_user is None and self.owner_group is None:
            raise ValueError('A document must be owned by a user or a group.')
           
        models.Model.save(self, force_insert, using=using)

    def get_absolute_url(self):
        return '/documents/%s/' % smart_unicode(self.id)
    
    def __unicode__(self):
        return self.title
    
    class Admin:
        search_fields = ['title']
  
    class Meta:
        verbose_name = _('document')
        verbose_name_plural = _('documents')
        
    def get_last_changed_for_user(self, user):
        version = Version.objects.order_by('-creation_time')[0]
        if (version):
            return version.creation_time
        else:
            return date()
            
    def get_latest(self):
        try: return Version.objects.filter(document=self.id).order_by('-id')[0]
        except Version.DoesNotExist: return None;

class Version(models.Model):
    document = models.ForeignKey(Document)
    title = models.CharField(max_length=1024,blank=True)
    contents = models.TextField(blank=True)
    owner = models.ForeignKey(User)
    creation_time = models.DateTimeField(auto_now_add=True, name=_('Creation time'))

    def get_absolute_url(self):
        return '/documents/%d/version/%d/' % (self.document.id, self.id)
        
    def save(self, force_insert=False, using=None):
        if self.title == '' and self.document.is_presentation == False:
            raise Exception('Versions must have a title.')
            
        models.Model.save(self, force_insert, using=using)

        self.document.title = self.title
        self.document.save()
    
    def __unicode__(self):
        if self.title == '':
            if self.document.owner_user is None:
                return 'Presentation for group '+unicode(self.document.owner_group)
            else:
                return 'Presentation for user '+unicode(self.document.owner_user)
        return self.title

    class Admin:
        search_fields = ['title']
    
    class Meta:
        verbose_name = _('version')
        verbose_name_plural = _('versions')
        ordering = ('-creation_time',)

def notify_version(sender, instance, **kwargs):
    if instance.document.title != '<Document without version>':
        notify(sender, instance=instance.document, **kwargs)

def notify_document(sender, instance, **kwargs):
    if instance.title != '<Document without version>':
        notify(sender, instance=instance, **kwargs)

signals.post_save.connect(notify_version, sender=Version)
signals.post_save.connect(notify_document, sender=Document)
