import re

from django.contrib.auth.models import Group
from django.core.validators import EmailValidator
from django.shortcuts import *
from django.contrib.auth import login
import django.forms
from django.contrib.auth.views import login_required
from curia import *
from curia.shortcuts import *
from curia.authentication.models import MetaUser, MetaGroup, Invite
from curia.authentication import get_everyone_group, get_public_user
from curia.documents.models import Document, Version
from curia.notifications.models import Bookmark, SubscriptionResult
from curia.labels.models import Label
from curia.registration.models import *
from curia.widgets import CheckboxInput


@login_required
def invite(request):    
    check_access(request.user, obj=request.community, command='administrate users')

    class InviteForm(django.forms.Form):
        emails =  django.forms.CharField(label=_('E-mail addresses of friends to invite'), help_text=_('Separate with comma to invite several people at once, e.g a@a.com, b@b.com'))
        message = django.forms.CharField(widget = django.forms.Textarea, required=False, label=_('Personal message'))
        
    if request.POST:
        form = InviteForm(request.POST)
        
        # validate emails
        email_seperator = re.compile(r'[ ,;]')
        emails = email_seperator.split(form.data['emails'])
        for email in emails:
            if email != '':
                if not EmailValidator(email):
                    form.errors['emails'].append(_('%s is not a valid email address') % email)
        
        if form.is_valid():
            emails = email_seperator.split(form.cleaned_data['emails'])
            message = form.cleaned_data['message']
                
            for email in emails:
                if email != '':                 
                    password = None
                    try:
                        user = User.objects.get(email=email)
                        if user in request.community.user_set.all():
                            continue
                        if user.is_active == False:
                            password = user.username
                    except User.DoesNotExist:
                        password = User.objects.make_random_password(20)
                        user = User.objects.create(email=email, username=password, is_active=False)     
                        user.set_password(password)
                        user.save()
                                    
                    if Invite.objects.filter(group=request.community, user=user, choice='-').count() == 0:
                        Invite.objects.create(user=user, group=request.community, inviter=request.user, message=message)

                    from django.template import loader, Context

                    t = loader.get_template('registration/email.html')
                    c = {
                        'password': password,
                        'email': email,
                        'domain': request.domain,
                        'inviter': request.user,
                        'message': form.data['message'],
                        'community': request.community,
                        } 
                    subject =  _('%s has invited you to %s') % (request.user, request.community)
                    html_message = t.render(Context(c))

                    from curia.html2text import html2text
                    from curia.mail import send_html_mail_with_attachments
                    text_message = html2text(html_message)
                    from django.contrib.sites.models import Site
                    send_html_mail_with_attachments(subject=subject, message=text_message, html_message=html_message, from_email='invite@'+Site.objects.get_current().domain, recipient_list=[email])

            return HttpResponseRedirect('/registration/')                
            
    else:
        form = InviteForm(initial={})
    
    return render_to_response(request, 'registration/index.html', {'form':form, 'invited':Invite.objects.filter(group=request.community, choice='-') })

def delete_invite(request, invite_id):
    check_access(request.user, obj=request.community, command='administrate users')

    Invite.objects.filter(pk=invite_id).delete()
     
    from django.utils.simplejson import dumps 
    return HttpResponse(dumps([invite_id], ensure_ascii=False), mimetype='text/json; charset=UTF-8')

def register(request):    
    class RegisterForm(django.forms.Form):
        email =  django.forms.CharField(label=_('E-mail address'))

    if request.POST:
        form = RegisterForm(request.POST)

        # validate email
        email = form.data['email']
        if not EmailValidator(email):
            form.errors['email'].append(_('%s is not a valid email address') % email)

        if form.is_valid():
            email = form.cleaned_data['email']

            password = None
            try:
                user = User.objects.get(email=email)
                return HttpResponseRedirect('/registration/request_new_password/')
            except User.DoesNotExist:
                password = User.objects.make_random_password(6)
                user = User.objects.create(email=email, username=User.objects.make_random_password(30), is_active=False)     
                user.set_password(password)
                user.save()

            if Invite.objects.filter(group=request.community, user=user, choice='-').count() == 0:
                Invite.objects.create(user=user, group=request.community, inviter=get_public_user(), message='')

            from django.template import loader, Context

            t = loader.get_template('registration/register_email.html')
            c = {
                'password': password,
                'email': email,
                'domain': request.domain,
                'community': request.community,
                } 
            subject =  _('Confirm e-mail for %s') % request.community
            html_message = t.render(Context(c))

            from curia.html2text import html2text
            from curia.mail import send_html_mail_with_attachments
            text_message = html2text(html_message)
            from django.contrib.sites.models import Site
            send_html_mail_with_attachments(subject=subject, message=text_message, html_message=html_message, from_email='register@'+Site.objects.get_current().domain, recipient_list=[email])

            return render_to_response(request, 'registration/register_email_sent.html', {})
    else:
        form = RegisterForm(initial={})

    return render_to_response(request, 'registration/register.html', {'form':form})

def email_sent(request):
    return render_to_response(request, 'registration/email_sent.html', {})
    
def accept(request):
    from django.conf import settings
    try:    REGISTRATION_FIELDS = settings.REGISTRATION_FIELDS
    except: REGISTRATION_FIELDS = ('name', 'birthday', 'gender', 'password')
    try:    REGISTRATION_DETAILS = settings.REGISTRATION_DETAILS
    except: REGISTRATION_DETAILS = ()
    
    class EnterCodeForm(django.forms.Form):
        if 'code' in request.REQUEST:
            if 'name' in REGISTRATION_FIELDS:
                first_name = django.forms.CharField(max_length=30,required=True, label=_('First name'))
                last_name = django.forms.CharField(max_length=30,required=True, label=_('Last name'))
            if 'birthday' in REGISTRATION_FIELDS:
                birthday = django.forms.DateField(required=False, label=_('Birthday'), help_text=_('Format is yyyy-MM-dd, e.g. 1980-05-27'))
            if 'gender' in REGISTRATION_FIELDS:
                gender = django.forms.ChoiceField(label=_('Gender'), choices=(('M', 'Male'), ('F', 'Female'),))
            if 'password' in REGISTRATION_FIELDS:
                password = django.forms.CharField(max_length=30,required=True,widget = django.forms.PasswordInput, label=_('Password'))
                confirm_password = django.forms.CharField(max_length=30,required=True,widget = django.forms.PasswordInput, label=_('Confirm password'))
            code = django.forms.CharField(max_length=30,required=True,widget = django.forms.HiddenInput, label=_('code'))
        else:
            password = django.forms.CharField(max_length=30,required=True,widget = django.forms.PasswordInput, label=_('Password'))
        email = django.forms.CharField(max_length=150,required=True,widget = django.forms.HiddenInput, label=_('email'))
        user_contract = django.forms.BooleanField(required=False, widget=CheckboxInput(attrs={'label':_('I have read and accepted the <a href="/registration/user_agreement/" target="blank">user agreement</a>')}), label='')

    if request.POST:
        form = EnterCodeForm(request.REQUEST)
        
        try: 
            form.data["user_contract"]
        except:
            form.errors['user_contract'] = (_("You must accept the user agreement."),)

        try:
            user = User.objects.get(email=request.REQUEST['email'])
            invites = Invite.objects.filter(group=request.community, user=user)
            if len(invites) == 0:
                form.errors['password'] = (_('You have not been invited to this community'),)
                
            if 'code' in request.REQUEST:
                if not user.check_password(request.REQUEST['code']):
                    raise User.DoesNotExist()
            else:
                if not user.check_password(request.REQUEST['password']):
                    raise User.DoesNotExist()
        except User.DoesNotExist:
            form.errors['password'] = (_('Username or password incorrect'),)            
        
        if 'code' in request.REQUEST and form.data['password'] != form.data['confirm_password']:
            form.errors['confirm'] = (_('Passwords did not match.'),)
            
        if form.is_valid():
            if 'code' in request.REQUEST:
                # set user details
                if 'name' in REGISTRATION_FIELDS:
                    user.first_name = form.cleaned_data["first_name"]
                    user.last_name = form.cleaned_data["last_name"]
                user.set_password(form.cleaned_data['password'])
                user.is_active = True
                user.save()
                
                if 'birthday' in REGISTRATION_FIELDS:
                    birthday = form.cleaned_data['birthday']
                else:
                    birthday = None
                if 'gender' in REGISTRATION_FIELDS:
                    gender = form.cleaned_data['gender']
                else:
                    gender = '-'
                meta_user = MetaUser.objects.create(user=user, birthday=birthday, gender=gender)
                #meta_user.picture = 'user-pictures/default_user_image.png'
                #meta_user.thumbnail = 'user-thumbnails/default_user_image.png'
                #meta_user.icon = 'user-icons/default_user_image.png'
                meta_user.language = 'sv'
                meta_user.save()
                
                if 'curia.notifications' in settings.INSTALLED_APPS:
                    Bookmark.objects.create(user=user, url='/users/'+str(user.id)+'/', title=user.first_name)
            
            for member in request.community.user_set.all():
                if member != user:
                    u = get_current_user()
                    if u.is_anonymous():
                        u = get_public_user()
                    SubscriptionResult.objects.create(user=member, content_type=get_content_type(user), object_id=user.pk, originator_user=u, originator_group=get_current_community())

            community = request.community
            community.user_set.add(user)
            community.save()
            everyone = get_everyone_group()
            everyone.user_set.add(user)
            everyone.save()

            #Create invite for each event in the group that has not already passed
            #start_span = start_of_day(datetime.now())-timedelta(hours=3)
            #end_span = start_span+timedelta(weeks=52)
            #active_events = Event.objects.filter(owner_group=community, start_time__lt=end_span, end_time__gt=start_span, repeat='', deleted=False)
            
            #for event in active_events:
            #    Reply.objects.create(inviter=community.meta.created_by, event=event, user=user)
                
            for invite in invites:
                invite.choice = 'Y'
                invite.save()
             
            from django.contrib.auth import authenticate
            user = authenticate(username=user.username, password=form.cleaned_data['password'])
            login(request, user)
            
            try:
                if community.meta.created_by == user and settings.REGISTRATION_SYSTEM == 'invite': 
                    return HttpResponseRedirect('%s/registration/' % community.get_absolute_url())
            except:
                pass
            try:
                return HttpResponseRedirect(settings.REGISTRATION_NEXT)
            except:
                return HttpResponseRedirect(community.get_absolute_url())
                
    else:
        initial = {}
        if 'code' in request.REQUEST:
            initial['code'] = request.REQUEST['code']
        initial['email'] = request.REQUEST['email']
        form = EnterCodeForm(initial=initial)
    
    return render_to_response(request, 'registration/enter_code.html', {'form': form, 'email':request.REQUEST['email'], 'disable_login_box':True})

def create_community(request):
    community_types = [
        ('Friends', _("Friends")),
        ('Organization', _("Organization")),
        ('Happening', _("Happening")),
        ('Project group', _("Project group")),
        ('Online group', _("Online group")),
        ('Other group', _("Other group"))
    ]
    
    class CreateForm(django.forms.Form):
        name = django.forms.CharField(min_length=4, label=_('Name of community'))
        domain = django.forms.CharField(min_length=4, label=_('Domain'), initial='', help_text='.eldmyra.se')
        email = django.forms.CharField(max_length=150,required=True, label=_('Your e-mail address'))
        confirm_email = django.forms.CharField(max_length=150,required=True, label=_('Confirm your e-mail address'))
        community_type = django.forms.ChoiceField(choices=community_types, label=_('Describe yourself'), widget = django.forms.RadioSelect)
        user_contract = django.forms.BooleanField(required=False, widget=CheckboxInput(attrs={'label':_('I have read and accepted the <a href="/registration/administrator_agreement/" target="blank">administrator agreement</a>')}), label='')

    if request.POST:
        form = CreateForm(request.POST)
        
        email = form.data["email"]
        if email != '':
            if not EmailValidator(email):
                form.errors['email'] = (_('%s is not a valid email address') % email,)
                        
        try: 
            form.data["user_contract"]
        except:
            form.errors['user_contract'] = (_("You must accept the user agreement."),)
        
        if form.data["email"] != form.data["confirm_email"]:
            form.errors['confirm_email'] = (_("Emails did not match."),)
        
        try:
            Group.objects.get(name=form.data["name"])
            form.errors['name'] = (_("That name is already taken."),)
        except Group.DoesNotExist:
            pass
        
        forbidden_names = ['support','login','administrator','administration','admin','administrate','administrering','administrera','eldmyra']
        for forbidden_name in forbidden_names:
            if form.data['name'].lower() == forbidden_name:
                form.errors['name'] = (_("You may not call your community %s.") % forbidden_name,)
                
        forbidden_domains = ['blogg','blog','start','community','eldmyra','admin','fest','rollspel','ninja','dota','administrering','administrera','student','hantverk','demo','test','support','login','administrator','administration']
        for forbidden_domain in forbidden_domains:
            if form.data['domain'].lower() == forbidden_domain:
                form.errors['domain'] = (_("You may not use the domain name %s.eldmyra.se") % forbidden_domain, )      

        try:
            user = User.objects.get(email=request.REQUEST['email'])
        except User.DoesNotExist:
            user = None
            
        try:
            MetaGroup.objects.get(domain=form.data['domain']+'.eldmyra.se')
            form.errors['domain'] = (_('Domain name is taken, please choose another'),)
        except MetaGroup.DoesNotExist:
            pass

        if form.is_valid():
            password = None
            new_user = False
            if not user:                
                # Create new user
                password = User.objects.make_random_password(6)
                user = User.objects.create(email=form.cleaned_data['email'], username=User.objects.make_random_password(30), is_active=False)     
                user.set_password(password)
                user.save()
                new_user = True

            community = Group.objects.create(name=form.cleaned_data['name'])
            meta_group = MetaGroup.objects.create(group=community, created_by=user, domain=form.cleaned_data['domain']+'.eldmyra.se')
            presentation = Document.objects.create(owner_group=community, is_presentation=True)
            new_version = Version(document=presentation,title='Presentation', contents='', owner=user)
            new_version.save()
            community.user_set.add(user)

            if new_user:
                Invite.objects.create(user=user, group=community, inviter=user, message='')

            from django.template import loader, Context

            t = loader.get_template('registration/community_email.html')
            c = {
                'password': password,
                'email': form.cleaned_data['email'],
                'domain': meta_group.domain,
                'inviter': None,
                'message': '',
                'community': community,
                } 
            subject =  _('Your community %s has been registered at Eldmyra.se!') % (community)
            html_message = t.render(Context(c))
            
            from curia.html2text import html2text
            from curia.mail import send_html_mail_with_attachments
            text_message = html2text(html_message)
            from django.contrib.sites.models import Site
            send_html_mail_with_attachments(subject=subject, message=text_message, html_message=html_message, from_email='invite@'+Site.objects.get_current().domain, recipient_list=[form.cleaned_data['email']])
            
            # Homepage / Do not create a homepage, the no external page view is default for new communitites
            #document = Document.objects.create(owner_group=community, owner_user=user, is_presentation=False)
            #new_version = Version(document=document,title='Hem', contents='', owner=user)
            #new_version.save()
            
            # set up access rights
            #from curia.authentication import grant_access, get_public_user
            #grant_access(command='view', user=get_public_user(), obj=document)
            
            # create menu item
            #from curia.homepage.models import MenuItem
            #MenuItem.objects.create(group=community, content_type=get_content_type(document), object_id=document.id, title='Hem', url=document.get_absolute_url(), order=0, parent=None)

            from curia.labels.models import SuggestedLabel
            from curia.forums.models import Thread
            SuggestedLabel.objects.create(title=_('Events'), label=_('Events'), group=community, created_by=user, content_type=get_content_type(Thread))
            SuggestedLabel.objects.create(title=_('Links'), label=_('Links'), group=community, created_by=user, content_type=get_content_type(Thread))

            Label.objects.create(object_id=community.id, deleted=False, name=form.cleaned_data['community_type'], content_type=get_content_type(community), created_by = user, owner_user=user, owner_group=community)
            
            if new_user:
                return render_to_response(request, 'registration/create_community_done.html', {'community':community, 'disable_login_box':True})
            else:
                return HttpResponseRedirect(community.get_external_absolute_url())
    else:
        form = CreateForm()

    return render_to_response(request, 'registration/create_community.html', {'form':form, 'disable_login_box':True})    

def request_new_password(request):
    class RequestForm(django.forms.Form):
        email = django.forms.CharField(max_length=150,required=True, label=_('Email'))
    
    if request.POST:
        form = RequestForm(request.REQUEST)
        try:
            user = User.objects.get(email=request.REQUEST['email'])
        except User.DoesNotExist:
            form.errors['email'] = (_('There is no user with this email'),)

        if form.is_valid():
            from django.template import loader, Context

            password = User.objects.make_random_password(6)
            email = form.cleaned_data['email']
            t = loader.get_template('registration/retrieve.html')
            c = {
                'password': password,
                'email': email,
                'domain': request.domain,
                } 
            subject =  _('New password request on Eldmyra.se')
            html_message = t.render(Context(c))

            from curia.html2text import html2text
            from curia.mail import send_html_mail_with_attachments
            text_message = html2text(html_message)
            from django.contrib.sites.models import Site
            send_html_mail_with_attachments(subject=subject, message=text_message, html_message=html_message, from_email='retrieve@'+Site.objects.get_current().domain, recipient_list=[email])

            try:
                forgot = ForgotPassword.objects.get(user=user)
                forgot.delete()
            except:
                pass
            ForgotPassword.objects.create(user=user, password=password, created_from='')

            return render_to_response(request, 'registration/request_email_sent.html')
    
    else:
        form = RequestForm(initial={})      
    
    return render_to_response(request, 'registration/request_new_password.html', {'form':form, 'disable_login_box':True})
    
def set_new_password(request):
    class NewPasswordForm(django.forms.Form):
        password = django.forms.CharField(max_length=30,required=True,widget = django.forms.PasswordInput, label=_('New password'))
        confirm_password = django.forms.CharField(max_length=30,required=True,widget = django.forms.PasswordInput, label=_('Confirm password'))
    
    if request.POST:
        form = NewPasswordForm(request.REQUEST)

        try:
            user = User.objects.get(email=request.REQUEST['email'])
            try:
                forgot = ForgotPassword.objects.get(user=user, password=request.REQUEST['code'])            
            except:
                raise User.DoesNotExist()
        except User.DoesNotExist:
            form.errors['password'] = (_('Username or password incorrect'),)            

        if form.data['password'] != form.data['confirm_password']:
            form.errors['confirm'] = (_('Passwords did not match.'),)

        if form.is_valid():
            user.set_password(form.cleaned_data['password'])
            user.save()
            forgot.delete()
            return HttpResponseRedirect('/')
    else:
        form = NewPasswordForm(initial={})
    
    return render_to_response(request, 'registration/set_new_password.html', {'form':form})
        