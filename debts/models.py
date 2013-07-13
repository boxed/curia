from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from curia import get_current_user
from datetime import datetime

def get_account_for_user(user):
    try:
        return user.account
    except Account.DoesNotExist:
        return Account.objects.create(user=user)

class Account(models.Model):
    user = models.OneToOneField(User, primary_key=True, verbose_name=_('User'))
    balance = models.DecimalField(decimal_places=2, max_digits=50, blank=False, default=0, verbose_name=_('Current balance'))
    
    def __unicode__(self):
        return _(u'%(user)s %(balance)s') % {'user':self.user, 'balance':self.balance}
    
    class Admin:
        pass
    
class Transaction(models.Model):
    description = models.CharField(max_length=1024,blank=True)
    from_user = models.ForeignKey(User, related_name='outgoing_transactions', verbose_name=_('From'))
    to_user = models.ForeignKey(User, related_name='incoming_transactions', verbose_name=_('To'))
    cost = models.DecimalField(decimal_places=2, max_digits=50, blank=False, verbose_name=_('Cost'))

    created_by = models.ForeignKey(User, related_name="created_transactions", verbose_name=_('Created by'))
    creation_time = models.DateTimeField(auto_now_add=True, verbose_name=_('Creation time'))

    rejected = models.BooleanField(default=False, verbose_name=_('Rejected'))
    rejected_by = models.ForeignKey(User, blank=True, null=True, default=None, related_name="rejected_transactions", verbose_name=_('Rejected by'))
    rejection_time = models.DateTimeField(blank=True, null=True, verbose_name=_('Rejection time'))
    rejected_description = models.CharField(max_length=1024,blank=True)
    
    def __unicode__(self):
        return u'%s -> %s (%s) - %s' % (self.from_user, self.to_user, self.description, 'rejected' if self.rejected else '')
    
    def save(self, force_insert, using):
        self.created_by = get_current_user()
        
        if self.from_user == get_current_user():
            self.accept()
        else:
            models.Model.save(self, force_insert, using=using)
    
    def accept(self):
        from_account = get_account_for_user(self.from_user)
        to_account = get_account_for_user(self.to_user)
        from_account.balance -= self.cost
        to_account.balance += self.cost
        from_account.save()
        to_account.save()
        models.Model.save(self)
        
    def reject(self):
        self.rejected = True
        self.rejected_by = get_current_user()
        self.rejection_time = datetime.now()
        from_account = get_account_for_user(self.from_user)
        to_account = get_account_for_user(self.to_user)
        from_account.balance += self.cost
        to_account.balance -= self.cost
        from_account.save()
        to_account.save()
        models.Model.save(self)

    class Admin:
        pass
