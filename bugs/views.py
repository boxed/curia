
from curia.shortcuts import *
from curia.authentication import check_access
from curia.bugs.models import *
from django.utils.translation import ugettext as _
from django.http import HttpResponseRedirect, HttpResponse
from curia import *

def report_bug(request):
    class ReportForm(django.forms.Form):
        description = django.forms.CharField(required=False, widget = django.forms.Textarea, label=_('Description'))
        
    if request.POST:
        form = ReportForm(request.POST)
        
        if form.is_valid():
            urls = get_string(request, 'urls')
            if 'HTTP_USER_AGENT' in request.META:
                user_agent = request.META['HTTP_USER_AGENT']
            else:
                user_agent = 'unknown'
            bug = Bug.objects.create(description=strip_p(form.cleaned_data['description']), reporter=request.user, browser=user_agent, urls=urls)
            
            from django.core.mail import send_mail
            from django.template import loader, Context

            t = loader.get_template('bugs/new_bug_admin_email.html')
            c = {'bug':bug} 
            subject =  _('%s has reported a bug') % request.user
            html_message = t.render(Context(c))
    
            from curia.html2text import html2text
            from curia.mail import send_html_mail_with_attachments
            text_message = html2text(html_message)
            from django.contrib.sites.models import Site
            from django.conf import settings
            send_html_mail_with_attachments(subject=subject, message=text_message, html_message=html_message, from_email='support@'+Site.objects.get_current().domain, recipient_list=[x[1] for x in settings.ADMINS])

            return HttpResponse('0')
    else:
        form = ReportForm(initial={})
    
    return HttpResponseRedirect(request, 'bugs/report.html', {'form':form})