from django.db import models
from django.contrib.auth.models import User,Group
from django.conf import settings
from django.db.models import signals
from django.dispatch import dispatcher
from django.utils.translation import ugettext_lazy as _
from curia.notifications import enable_notifications
import os

class Image(models.Model):
    title = models.CharField(max_length=1024, verbose_name=_('Title'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    width = models.IntegerField(blank=True, null=True, verbose_name=_('Width'))
    height = models.IntegerField(blank=True, null=True, verbose_name=_('Height'))
    image = models.ImageField(width_field='width', height_field='height', upload_to='images', verbose_name=_('Image'))
    owner_user = models.ForeignKey(User, blank=True, null=True, verbose_name=_('Owner user'))
    owner_group = models.ForeignKey(Group, blank=True, null=True, verbose_name=_('Owner group'))
    creation_time = models.DateTimeField(auto_now_add=True, verbose_name=_('Creation time'))
    deleted = models.BooleanField(default=False, verbose_name=_('Deleted'))
    deleted_by = models.ForeignKey(User, blank=True, null=True, default=None, related_name="deleted_images", verbose_name=_('Deleted by'))
    deletion_time = models.DateTimeField(blank=True, null=True, verbose_name=_('Deletion time'))
    
    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return '/images/%i/' % self.id
    
    class Admin:
        search_fields = ['title', 'description']

    class Meta:
        verbose_name = _('image')
        verbose_name_plural = _('images')

class ImageSet(models.Model):
    title = models.CharField(max_length=1024, verbose_name=_('Title'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    images = models.ManyToManyField(Image, blank=True, verbose_name=_('Images'), related_name='sets')
    representative_image = models.ForeignKey(Image, blank=True, null=True, verbose_name=_('Representative image'), related_name='represented_in_sets')
    owner_user = models.ForeignKey(User, blank=True, null=True, verbose_name=_('Owner user'))
    owner_group = models.ForeignKey(Group, blank=True, null=True, verbose_name=_('Owner group'))
    creation_time = models.DateTimeField(auto_now_add=True, verbose_name=_('Creation time'))
    number_of_images = models.IntegerField(verbose_name=_('Number of images'), default=0)
    deleted = models.BooleanField(default=False, verbose_name=_('Deleted'))
    deleted_by = models.ForeignKey(User, blank=True, null=True, default=None, related_name="deleted_sets", verbose_name=_('Deleted by'))
    deletion_time = models.DateTimeField(blank=True, null=True, verbose_name=_('Deletion time'))

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return '/images/sets/%s/' % self.id

    class Admin:
        pass
        
    class Meta:
        ordering = ('-creation_time',)
        verbose_name = _('image set')
        verbose_name_plural = _('images sets')

def set_image_size(sender, instance, **kwargs):
    from PIL import Image
    # This function is called twice for file uploads, because the object is saved twice: once without the file on 
    # disk and one with. We ignore the first save by checking if the filename has been set yet
    if instance.image:
        image = Image.open(instance.image.path)
        image.thumbnail(settings.THUMBNAIL_SIZE, Image.ANTIALIAS)
        image.save(instance.image.path.replace(os.sep+'images'+os.sep, os.sep+'thumbnails'+os.sep))
        image = Image.open(instance.image.path)
        image.thumbnail(settings.IMAGE_SIZE, Image.ANTIALIAS)
        image.save(instance.image.path)
    
signals.post_save.connect(set_image_size, sender=Image)

enable_notifications(ImageSet)