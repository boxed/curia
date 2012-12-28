import unittest
from curia.authentication.models import *
from curia.bugs.models import *
from curia.calendars.models import *
from curia.documents.models import *
from curia.files.models import *
from curia.forums.models import *
from curia.images.models import *
from curia.notifications.models import *
from curia.registration.models import *
from curia import *
from django.contrib.auth.models import User, Group
from django.test.client import Client, MULTIPART_CONTENT
from django.test import TestCase
from django.core import mail
import re
from django.utils.encoding import smart_unicode

def decorate_community_aware_post(old_request):
    def community_aware_request(self, path, data={}, content_type=MULTIPART_CONTENT, **extra):
        if not hasattr(self, 'community'):
            self.community = 'test'
        extra.update(HTTP_HOST='%s.eldmyra.se' % self.community)
        return old_request(self, path, data, content_type, **extra)
    return community_aware_request

def decorate_community_aware_get(old_request):
    def community_aware_request(self, path, **extra):
        if not hasattr(self, 'community'):
            self.community = 'test'
        extra.update(HTTP_HOST='%s.eldmyra.se' % self.community)
        return old_request(self, path, **extra)
    return community_aware_request
    
Client.post = decorate_community_aware_post(Client.post)
Client.get = decorate_community_aware_get(Client.get)

def split_url_and_params(url):
    url, raw_params = url.split('?')
    params = {}
    for raw_param in raw_params.split('&'):
        name, value = raw_param.split('=')
        params[name] = value
    return (url, params)

def login(client, email, password, expected_code=302):
    community = client.community
    response = client.post('/login/', {'username':email, 'password':password})
    if response.status_code != expected_code:
        print response.content
        raise 'login did not return expected code (return code: %s, expected: %s)' % (response.status_code, expected_code)
    if expected_code == 302:
        if response['Location'] != 'http://community.%s.eldmyra.se/' % community:
            raise 'login did not redirect to community.%s.eldmyra.se (redirected to: %s)' % (community, response['Location'])
        client.user = User.objects.get(email=email)
    return response
    
all_classes = [Bug, Message, Thread, Image, ImageSet, Event, File]
new_notification_classes = [Thread, ImageSet, Event, File]
    
class CuriaTest(TestCase):
    def setUp(self):
        # create superuser
        self.superuser = User(
            username='superuser', 
            first_name='Super', 
            last_name='User', 
            email='superuser@killingar.net',
            is_staff=True,
            is_superuser=True)
        self.superuser.set_password('superuserpassword')
        self.superuser.save()
        MetaUser.objects.create(user=self.superuser, inviter=None, birthday=None)
        
    def tearDown(self):
        self.delete_all_objects()

    def delete_all_objects(self):
        for cls in [File, Image, Message, Thread, Bug, Event, ImageSet]:
            cls.objects.all().delete()
        # TODO: make the watchers handle true database delete of objects, not just delete marking
        #self.assertEqual(Watcher.objects.all().count(), 0)
        Watcher.objects.all().delete() # HACK: when the above is done, remove this line
        # TODO: make the subscription result handle true database delete of objects, not just delete marking
        #self.assertEqual(SubscriptionResult.objects.all().count(), 0)
        SubscriptionResult.objects.all().delete()
        # TODO: make the notifications handle true database delete of objects, not just delete marking
        #self.assertEqual(Notification.objects.all().count(), 0)
        Notification.objects.all().delete()
        self.assertEqual(Watcher.objects.all().count(), 0)
        self.assertEqual(SubscriptionResult.objects.all().count(), 0)
        self.assertEqual(Notification.objects.all().count(), 0)
    
    def create_user(self, inviter, email, password, community):
        old_user_count = User.objects.all().count()
        self.invite(inviter, email)
        client = self.answer_invitation_email(community, password)
        self.assertEquals(User.objects.all().count(), old_user_count+1)
        return client
    
    #def create_community(self, name, email, label):
        #old_group_count = Group.objects.all().count()
        # Send email
        # Answer email and register
        #self.assertEquals(Group.objets.all().count(), old_user_count+1)
        #return something
        
    def check_access(self, command, client, objects, fail=[]):
        for key in objects:
            if hasattr(objects[key], 'get_absolute_url'):
                url = objects[key].get_absolute_url()
                if command != 'view':
                    url +=  command+'/'
                request = client.get(url)
                if key not in fail:
                    if command == 'view':
                        self.assertEquals(request.status_code, 200, 'view on: '+url)
                    else:
                        self.assert_(request.status_code == 302 or 'text/json' in request.REQUEST['Content-Type'], '%s on %s: status_code %s, Content-Type %s' % (command, url, request.status_code, request.REQUEST['Content-Type']))
                else:
                    self.assert_(request.status_code == 403 or request.status_code == 500, '%s on %s: status_code %s' % (command, url, request.status_code))
            else:
                print 'warning: no %s code for %s' % (command, key)

    #def test_with_coverage(self):
    #         import coverage
    #         coverage.erase()
    #         coverage.start()
    #         import curia
    #         self._test_all()
    #         coverage.stop()
    #         TODO: coverage only generates reports on __init__, not submodules!
    #         coverage.report([
    #             curia,
    #             curia.base, 
    #             curia.authentication, 
    #             curia.bugs, 
    #             curia.calendars, 
    #             curia.documents, 
    #             curia.files, 
    #             curia.forums,
    #             #curia.homepage, 
    #             curia.images,
    #             curia.labels,
    #             curia.notifications,
    #             curia.registration,
    #             curia.times,
    #             ], show_missing=0)

    def test_all(self):
        # create the first community the manual way
        self.community = Group.objects.create(name='test')
        MetaGroup.objects.create(group=self.community, created_by=self.superuser, domain='test.eldmyra.se')

        self.superuser_client = Client()

        self.superuser_client.community = 'test'
        login(self.superuser_client, self.superuser.email, 'superuserpassword')

        # "eldmyra" community is special as it is used by the external page
        Group.objects.create(name='eldmyra')

        # create users
        self.admin_client = self.create_user(inviter=self.superuser_client, email='admin@killingar.net', password='adminuserpassword', community='test')
        self.user_client = self.create_user(inviter=self.superuser_client, email='user@killingar.net', password='userpassword', community='test')
        self.user_client2 = self.create_user(inviter=self.superuser_client, email='user2@killingar.net', password='user2password', community='test')
        self.user_client3 = self.create_user(inviter=self.superuser_client, email='user3@killingar.net', password='user3password', community='test')
        self.assertEqual(SubscriptionResult.objects.all().count(), 6) # 6 = SubscriptionResults from the joining: 0+1+2+3
        SubscriptionResult.objects.all().delete()
        
        # check that the user cannot invite people
        self.invite(self.user_client, email='user4@killingar.net', fail=True)

        # login tests
        client = Client()
        client.community = 'test'
        login(client, 'fake@email', 'superuserpassword', expected_code=200) # Try to log in with a username that does not exist but a password that does
        login(client, self.superuser.email, 'blabla', expected_code=200) # Try to log in with the an existing user but a password that does not exist
        login(client, 'fake@email', password='Notapassword', expected_code=200) # Try to log in with neither password or username existing
        login(client, self.superuser.email, password='adminuserpassword', expected_code=200) # Try to log in with an existing user using another existing users password

        # check that test.eldmyra.se shows normally
        self.assertContains(self.user_client.get('/'), 'site-media/login_background.jpg')
        
        # create another community with a new user: test2
        self.create_community('test2', 'test2user@killingar.net')
        
        # TODO: create another community with an existing user: test3
        
        # TODO: create users for test2

        # set all the users to view the inside community
        self.user_client.community = 'community.test'
        self.superuser_client.community = 'community.test'
        self.admin_client.community = 'community.test'

        # check that community.test.eldmyra.se leads to the portal
        self.assertContains(self.user_client.get('/'), 'Portal')

        # create objects
        objects = self.create_objects(self.user_client)
        # check that the creator user did not get SubscriptionResults
        self.assertEqual(SubscriptionResult.objects.filter(user=self.user_client.user).count(), 0)
        # check that all the non-creators got SubscriptionResults
        self.assertEqual(SubscriptionResult.objects.all().count(), len(new_notification_classes)*(Group.objects.get(name='test').user_set.count()-1)) # notifications = things to watch * (members - the creator)
        # check that the admin got SubscriptionResults for each created object
        for key in objects:
            if key not in [Bug]: # ignore list
                url = '/notifications/new/%s/' % get_content_type(key).id
                s = u'%s' % objects[key]
                content = smart_unicode(self.admin_client.get(url).content)
                self.assert_(s in content, u'new object list for %s broken: %s not in %s' % (str(key), s, content))
        # TODO: check that members of other communities didn't get notifications
        # TODO: notifications
        # TODO: check that a user from another community cannot view the objects
        # TODO: check that an admin from another community cannot view the objects
        self.check_access('view', self.user_client, objects) # check that the user can view them all
        self.check_access('view', self.admin_client, objects) # check that the admin can view them all
        self.check_access('view', self.superuser_client, objects) # check that the superuser can view them all
        self.check_access('delete', self.superuser_client, objects) # check that the superuser can delete them all
        self.delete_all_objects()
        
        # check that a user can reply to thread he did not create
        objects = self.create_objects(self.user_client)
        self.assertEqual(Message.objects.all().count(), 2)
        self.create_object(self.user_client2, objects, Message, objects[Thread].get_absolute_url(), {'body':'body', 'parent_message_id':objects[Message].id})
        self.assertEqual(Message.objects.all().count(), 3)
        self.delete_all_objects()        
        
        objects = self.create_objects(self.user_client)
        self.check_access('delete', self.user_client, objects) # check that the user can delete the objects
        self.delete_all_objects()

        objects = self.create_objects(self.user_client)
        self.check_access('delete', self.admin_client, objects, fail=all_classes) # check that another user cannot delete the objects
        self.delete_all_objects()
        
        administration_content_types = [
            ('thread', [Thread, Message]),
            ('file', [File]),
            ('image_set', [ImageSet, Image]),
            ('event' , [Event]),
            #'homepage', [?]),
        ]
        
        for domain in administration_content_types:
            objects = self.create_objects(self.user_client)
            old_number_of_objects = 0
            old_number_of_objects = sum([cls.objects.filter(deleted=False).count() for cls in domain[1]])
            self.superuser_client.post('/administration/', {'new_%s' % domain[0]:'checked', 'new_user_id':self.admin_client.user.id}) # add domain admin rights to admin
            self.check_access('delete', self.admin_client, objects, fail=set(all_classes)-set(domain[1])) # check that the admin can delete things in the domain but not anything else
            new_number_of_objects = sum([cls.objects.filter(deleted=False).count() for cls in domain[1]])
            if not old_number_of_objects > new_number_of_objects:
                print domain
            self.assert_(old_number_of_objects > new_number_of_objects)
            self.delete_all_objects()
            
        # TODO: check that an admin from community X cannot view or delete objects in community Y

        # user settings
        # change presentation and set user image
        # remove user image
        # change password
        # homepage administration
        # bookmarks
        # notifications (check that they don't leak across community borders!)
        
        # create a second community
        # invite an existing user to the community

        # log out
        self.assertEqual(self.superuser_client.get('/logout/').status_code, 302)
        
    def create_object(self, client, objects, cls, url, attribs, expected_status_code=302, items_to_create=1):
        old_count = cls.objects.all().count()
        response = client.post(url, attribs)
        if response.status_code != expected_status_code:
            print response.content
        self.assertEqual(response.status_code, expected_status_code)
        self.assertEqual(cls.objects.all().count(), old_count+items_to_create)
        obj = cls.objects.all()[cls.objects.all().count()-1]
        objects[cls] = obj
        
        self.assertEqual(get_owner(obj) == client.user or get_owner(obj) == None, True)
        self.assertEqual(get_community_of(obj) == Group.objects.get(name='test') or get_community_of(obj) == None, True)
        
        ignore_list = ['first_message']

        for key in attribs:
            if key.endswith('time_0'):
                # TODO: this is a split date/time field, validate it specially
                continue
                
            if key.endswith('time_1'):
                continue # just ignore the second field of the split date/time duo
            
            if key in ignore_list:
                continue
                
            if key == 'labels':
                # TODO: check labels
                continue
            
            if isinstance(attribs[key], file):
                attribs[key].close()
                continue
                
            self.assertEqual(getattr(obj, key), attribs[key])
    
    def create_objects(self, client):
        objects = {}
        self.create_object(client, objects, Bug, '/bugs/report/', {'description':'descriptionbug', 'urls':'/'}, 200)
        self.create_object(client, objects, Event, '/calendars/groups/1/add/', {'title':'titleevent', 'labels':'foo', 'description':'descriptionevent', 'start_time_0':'2008-01-01', 'start_time_1':'10:40'})
        
        self.create_object(client, objects, File, '/files/add/', {'title':'title', 'labels':'labels', 'description':'descriptionfile', 'file':open('test/foo.png')})
        
        # images
        self.create_object(client, objects, ImageSet, '/images/groups/1/sets/add/', {'title':'titleimageset', 'labels':'labels', 'description':'descriptionimageset'})
        # normal image upload
        self.create_object(client, objects, Image, objects[ImageSet].get_absolute_url()+'add/', {'description':'descriptionimage', 'image':open('test/foo.png')})
        # zip file upload
        self.create_object(client, objects, Image, objects[ImageSet].get_absolute_url()+'add/', {'description':'descriptionfile', 'image':open('test/multi-images-test.zip')}, items_to_create=4)
        
        # forum tests
        self.assertEqual(Message.objects.all().count(), 0)
        self.assertEqual(Thread.objects.all().count(), 0)
        self.create_object(client, objects, Thread, '/forums/add/', {'name':'name', 'labels':'labels', 'first_message':'first message'}, 302)
        self.assertEqual(Message.objects.all().count(), 1)
        objects[Message] = Message.objects.all()[0]
        self.assertEqual(objects[Message].body, 'first message')
        self.assertEqual(objects[Message].parent_thread, objects[Thread])
        
        # reply to thread
        self.create_object(client, objects, Message, objects[Thread].get_absolute_url(), {'body':'body', 'parent_message_id':objects[Message].id})
        self.assertEqual(Message.objects.all().count(), 2)
        
        return objects

    def invite(self, inviter_client, email, message='hey yo', fail=False):
        self.assertEqual(Invite.objects.filter(choice='-').count(), 0)
        expected_code = 302
        if fail:
            expected_code = 403
        self.assertEquals(inviter_client.post('/registration/', {'emails':email, 'message':message}).status_code, expected_code)
        if fail:
            self.assertEqual(len(mail.outbox), 0)
        else:
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(Invite.objects.filter(choice='-').count(), 1)
            self.assertEqual(message in mail.outbox[0].html_message, True)
            self.assertEqual(mail.outbox[0].to[0], email)
            self.assertEqual(unicode(inviter_client.user) in mail.outbox[0].subject, True)

    def answer_invitation_email(self, community, password):
        invitation_url = re.compile(r'%s\.eldmyra\.se(.*?)"' % community).search(mail.outbox[0].html_message).groups(0)[0].replace('&amp;', '&')
        invitation_url, params = split_url_and_params(invitation_url)

        new_client = Client()
        new_client.community = 'test'
        response = new_client.post(invitation_url, {'first_name':params['email'].replace('@', '_').replace('.', '_'), 'last_name':'User', 'birthday':'1980-04-17', 'gender':'M', 'password':password, 'confirm_password':password, 'email':params['email'], 'email':params['email'], 'code':params['code'], 'user_contract':'checked'})
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response['Location'], 'http://community.%s.eldmyra.se/' % new_client.community)
        new_client.user = User.objects.get(email=params['email'])
        del mail.outbox[0]
        return new_client

        # TODO: implement admin and user clients
        #self.admin_client = Client()
        #self.user_client = Client()
        #pass

    def create_community(self, name, email):
        old_user_count = User.objects.all().count()
        old_group_count = Group.objects.all().count()
        client = Client()
        client.community = 'eldmyra'
        response = client.post('/create_community/', {'name':name, 'domain':name+'.eldmyra.se', 'email':email, 'confirm_email':email, 'community_type':'Friends', 'user_contract':'checked'})
        self.assertEquals(response.status_code, 200)
        #self.assertContains(response.contents, '%s.eldmyra.se' % name)
        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(old_group_count+1, Group.objects.all().count())
        self.assertEquals(old_user_count+1, User.objects.all().count())
        del mail.outbox[0]

    def footest_details(self):
        #=============
        #Presentation test
        #Try changing the presentation and check that it is changed. Also check that name changes correctly.
        self.client.post('/users/1/edit/', {'firstname': 'John', 'lastname': 'Doe', 'birthday':'1983-09-22', 'labels': '', 'presentation': 'My name is John Doe.'})
        response = self.client.get('/users/1/')
        self.assertContains(response, 'My name is John Doe', count=1, status_code=200)  #Failed to change presentation-text of User1               
        try:
            user = User.objects.get(first_name='John')
        except:
            Fail    #Failed to change the first name of User1 to John.
        self.failUnlessEqual(user.last_name, 'Doe')     #Failed to change the last name of User1 to Doe.

        #=============
        #Document tests
        #Try creating a document without title and make sure the error message is displayed.
        response = self.client.post('/documents/add/', {'user_id': 1, 'title': '', 'labels':'', 'contents': ''})
        self.assertContains(response, 'obligatoriskt', count=1, status_code=200)    #The error message for trying to create a document without title was not displayed  

        #Try creating a document and then check that it exists.
        response = self.client.post('/documents/add/', {'user_id': 1, 'title': 'Document1', 'labels':'', 'contents': 'Text in document1.'})
        try:
            document1 = Document.objects.get(title='Document1')
        except:
            Fail    #Failed to create a new document named Document1

        #Try changing the document and check that it worked.
        response = self.client.post('/documents/1/edit/', {'title': 'Changed document1', 'labels':'', 'contents': 'The text in document1 has now been changed.', 'edit_version': 1})
        try:
            document1 = Document.objects.get(title='Changed document1')
        except:
            Fail    #Failed to change the name of Document1 to "Changed document1"
        self.assertContains(response, 'The text in document1 has now been changed.', count=1, status_code=200)  #Failed to change the content of Document1
        
        #Try removing the document
        response = self.client.post('/documents/1/delete/')
        try:
            document1 = Document.objects.get(title='Changed document1', deleted=True)
        except:
            Fail    #Failed to delete Changed document1"
