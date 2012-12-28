import os
from curia import settings
from datetime import datetime
os.environ['DJANGO_SETTINGS_MODULE'] = 'curia.settings'
from django.utils.translation import ugettext as _

# clean up session data
from django.bin.daily_cleanup import clean_up
clean_up()

# mail user notifications
from curia.mail import send_html_mail_with_attachments
from django.template import loader, Context
from django.contrib.sites.models import Site

from curia.notifications import get_users_to_email
from curia.notifications.models import Notification, SubscriptionResult
users = get_users_to_email()
#from django.contrib.auth.models import User
#users = [User.objects.get(pk=1)]

import codecs
log = codecs.open('curia_schedule.log', 'w', 'utf-8')

for user in users:
    if user.email != '':
        new_stuff = {}
        for community in user.groups.exclude(name='everyone'):
            notifications = Notification.objects.filter(user=user, originator_group=community)
            from curia.notifications import get_subscription_entries
            subscription_entries = get_subscription_entries(user, community)
    
            if len(notifications) != 0 or len(subscription_entries) != 0:
                new_stuff[community] = {'notifications':notifications, 'subscription_entries':subscription_entries}
        
        if len(new_stuff) != 0:
            communities = u', '.join([unicode(x) for x in new_stuff.keys()])
            c = {'new_stuff':new_stuff, 'communities':communities}
            subject =  _("%s has something new for you") % communities
            html_message = loader.get_template('notification_email.html').render(Context(c))
            text_message = loader.get_template('notification_email.txt').render(Context(c))
            send_html_mail_with_attachments(subject=subject, message=text_message, html_message=html_message, from_email='no-reply@eldmyra.se', recipient_list=[user.email])
            meta = user.meta
            meta.last_notification_email_time = datetime.now()
            meta.save()
            log.write(u'sent to %s\n' % user)
    else:
        log.write(u'user %s has no email address\n' % user)

# mail user reminders for events

log.close()