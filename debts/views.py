from django.contrib.auth.views import login_required
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseServerError
import django
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from curia.shortcuts import *
from curia.debts.models import *
from decimal import Decimal

def send_notification_mail(user, transaction):
    if transaction.rejected:
        subject =  _('%s has rejected a debt') % user
        template = 'debts/transaction_rejected_email.html'
        recipient = transaction.to_user
    else:
        subject =  _('%s has added a debt') % user
        template = 'debts/transaction_added_email.html'
        recipient = transaction.from_user
    account = get_account_for_user(recipient)

    from django.core.mail import send_mail
    from django.template import loader, Context
    
    if account.balance == 0:
        status = 'neutral'
    elif account.balance < 0:
        status = 'negative'
    else:
        status = 'positive'

    t = loader.get_template(template)
    html_message = t.render(Context({'transaction':transaction, 'user':user, 'account':account, 'status':status} ))

    from curia.html2text import html2text
    from curia.mail import send_html_mail_with_attachments
    text_message = html2text(html_message)
    
    from django.contrib.sites.models import Site
    send_html_mail_with_attachments(subject=subject, message=text_message, html_message=html_message, from_email='debts@'+Site.objects.get_current().domain, recipient_list=[recipient.email])


@login_required
def index(request):
    class AddForm(django.forms.Form):
        from_user = django.forms.CharField(max_length=2048, label='', required=False)
        description = django.forms.CharField(max_length=2048, label='', required=False)
    
    if request.POST:
        form = AddForm(request.POST)
        # validate from_user
        first_name, last_name = form.data['from_user'].rsplit(' ', 1)
        from_user = User.objects.get(first_name__iexact=first_name, last_name__iexact=last_name)
        
        # validate the number
        tmp = form.data['description'].split(' ', 1)
        if len(tmp) < 1:
            form.errors['description'] = [_('Description must not be empty')]
        else:
            try:
                cost = Decimal(tmp[0])
            except:
                form.errors['description'] = [_('Description must start with the amount')]
            
        if form.is_valid():
            transaction = Transaction.objects.create(to_user=request.user, from_user=from_user, cost=cost, description=form.cleaned_data['description'])
            transaction.accept()
            
            send_notification_mail(request.user, transaction)

            return HttpResponseRedirect('/debts/')
    else:
        form = AddForm(initial={})
    
    try:
        account = Account.objects.get(user=request.user)
    except Account.DoesNotExist:
        account = Account(user=request.user)
        
    if account.balance < 0:
        top_users = Account.objects.filter(balance__gt=0).order_by('-balance')[:5]
    else:
        top_users = Account.objects.filter(balance__lt=0).order_by('balance')[:5]
        
    if account.balance == 0:
        status = 'neutral'
    elif account.balance < 0:
        status = 'negative'
    else:
        status = 'positive'
        
    return render_to_response(
        request, 
        'debts/index.html', 
        {
            'account':account, 
            'top_users':top_users, 
            'status':status,
            'rejected_transactions':Transaction.objects.filter(to_user=request.user, rejected=True).exclude(rejected_by=request.user),
            'form':form,
        })

@login_required    
def view_log(request):
    from django.db.models import Q
    if request.user.is_superuser and 'all' in request.REQUEST:
        transactions = Transaction.objects.all()
    else:
        transactions = Transaction.objects.filter(Q(from_user=request.user)|Q(to_user=request.user)).order_by('-creation_time')
    return render_to_response(request, 'debts/view_log.html', {'transactions':transactions})

@login_required
def view_positive_users(request):
    return render_to_response(request, 'debts/positive_users.html', {'accounts':Account.objects.filter(balance__gt=0).order_by('-balance')})

@login_required
def view_negative_users(request):
    return render_to_response(request, 'debts/negative_users.html', {'accounts':Account.objects.filter(balance__lt=0).order_by('-balance')})

@login_required
def clear_rejected(request):
    Transaction.objects.filter(to_user=request.user, rejected=True).exclude(rejected_by=request.user).delete()
    return HttpResponseRedirect('/debts/')

@login_required
def reject_transaction(request, transaction_id):
    transaction = Transaction.objects.get(pk=transaction_id)
    if transaction.from_user != request.user and transaction.to_user != request.user:
        raise Exception('transaction must be rejected by %s or %s' % (transaction.from_user, transaction.to_user))
    transaction.reject()
    send_notification_mail(transaction, request)
    return HttpResponseRedirect('/debts/')
    
def api_list(request):
    # TODO: validate user name/password
    return HttpResponse('\n'.join(['%s\t%s\t%s' % (account.user.email, account.user, account.balance) for account in Account.objects.filter().order_by('-balance')]))

def api_add(request):
    from curia import _thread_locals
    try:
        to_user = User.objects.get(email=request.REQUEST['email'])
        from_user = User.objects.get(email=request.REQUEST['from_user'])
        # TODO: validate user name/password
        # to_user = authenticate(username=username, password=request.REQUEST['password'])
    except User.DoesNotExist, e:
        return HttpResponseServerError('error: no such user')
    _thread_locals.request = request
    _thread_locals.user = to_user

    amount = eval(request.POST['calculation'],{"__builtins__":None},{})
    transaction = Transaction.objects.create(to_user=to_user, from_user=from_user, cost=amount, description=request.POST['calculation']+' from an iPhone')
    transaction.accept()
    send_notification_mail(to_user, transaction)
    return HttpResponse(amount)
