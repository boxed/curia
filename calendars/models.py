from django.db import models
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext_lazy as _
from curia.notifications import enable_notifications, notify
from django.db.models import signals
from django.dispatch import dispatcher

class Event(models.Model):
    owner_user = models.ForeignKey(User, blank=True, null=True, verbose_name=_('Owner user'))
    owner_group = models.ForeignKey(Group, blank=True, null=True, verbose_name=_('Owner group'))
    creation_time = models.DateTimeField(auto_now_add=True, verbose_name=_('Creation time'))
    deleted = models.BooleanField(default=False, verbose_name=_('Deleted'))
    deleted_by = models.ForeignKey(User, blank=True, null=True, default=None, related_name='deleted_events', verbose_name=_('Deleted by'))
    deletion_time = models.DateTimeField(blank=True, null=True, verbose_name=_('Deletion time'))
    event_parent = models.ForeignKey('self', blank=True, null=True, default=None, related_name='event_children', verbose_name=_('Event parent'))

    title = models.CharField(max_length=1024, verbose_name=_('Title'))
    description = models.TextField(blank=True, verbose_name=_('Description'))

    start_time = models.DateTimeField(verbose_name=_('Start time'))
    end_time = models.DateTimeField(verbose_name=_('End time'))
    all_day = models.BooleanField(default=False, verbose_name=_('All day'))
    REPEAT_CHOICES = (
        ('D', _('Day')),
        ('W', _('Week')),
        ('M', _('Month')),
        ('Y', _('Year')),
    )
    repeat = models.CharField(max_length=1, choices=REPEAT_CHOICES, blank=True, verbose_name=_('Repeat'))
    end_repeat = models.DateTimeField(blank=True, null=True, verbose_name=_('End repeat'))
    
    def get_absolute_url(self):
        return '/calendars/events/%d/' % self.id
    
    def __unicode__(self):
        return self.title
        
    def formatted_date(self):
        from curia import relative_pair_date_formatting
        return relative_pair_date_formatting(self.start_time, self.end_time)
    
    class Admin:
        search_fields = ['title']
        
    class Meta:
        verbose_name = _('event')
        verbose_name_plural = _('events')
        ordering = ('start_time',)

    def json_serialize(self):
        return {'id':self.id, 'title':self.title, 'description':self.description, 'start_time':self.start_time, 'end_time':self.end_time, 'end_repeat':self.end_repeat, 'all_day':self.all_day}
    
    def get_days_left(self):
        import datetime
        # TODO: this should be the day closest to today, this is different from the following code because events have a length 
        diff = self.start_time.date()-datetime.date.today()
        if diff.days == 0:
            return _('today')
        
        if diff.days == 1:
            return _('tomorrow')
        
        return unicode(_('%s days')) % diff.days

    def number_of_Y(self):
        return Reply.objects.filter(event=self, choice='Y').count()

    def number_of_N(self):
        return Reply.objects.filter(event=self, choice='N').count()

    def number_of_unknown(self):
        return Reply.objects.filter(event=self, choice='?').count()

    def number_of_noanswer(self):
        return Reply.objects.filter(event=self, choice='-').count()

    def user_answer(self):
        try:
            from curia import get_current_user
            return Reply.objects.get(event=self, user=get_current_user())
        except Reply.DoesNotExist:
            return Reply(event=self, choice='-')

enable_notifications(Event)

def notify_event(sender, instance, **kwargs):
    if instance.event_parent == None:
        notify(sender, instance)

signals.post_save.connect(notify_event, sender=Event)

class Reply(models.Model):
    REPLY_CHOICES = (
        ('Y', _('Yes')),
        ('N', _('No')),
        ('?', _('Unsure')),
        ('-', _('No reply')),
    )
    
    event = models.ForeignKey(Event, verbose_name=_('Event'))
    user = models.ForeignKey(User, related_name='event_replies', verbose_name=_('User'))
    inviter = models.ForeignKey(User, related_name='event_invited_users', verbose_name=_('Inviter'))
    choice = models.CharField(max_length=1, choices=REPLY_CHOICES, default='-', verbose_name=_('Choice'))
    comment = models.CharField(max_length=767, blank=True, verbose_name=_('Comment'))
    
    def __unicode__(self):
        if self.choice == '-':
            return u'%s hasn\'t replied to %s' % (self.user, self.event)
        else:
            return u'%s replied "%s" to %s' % (self.user, self.choice, self.event)

    class Admin:
        search_fields = ['user__username']

    class Meta:
        verbose_name = _('reply')
        verbose_name_plural = _('replies')