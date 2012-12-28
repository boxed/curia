# -*- coding: UTF-8

from django.contrib.auth.models import *
from curia.authentication.models import *
from curia.authentication import get_everyone_group
from curia import get_content_type
import base64

def fix_string(s):
    import codecs
    utf8 = codecs.getdecoder('UTF8')
    s = s.replace('\x80', utf8("£")[0].encode('latin1'))
    s = s.replace('\x85', utf8("...")[0].encode('latin1'))
    s = s.replace('\x86', utf8("-")[0].encode('latin1'))
    s = s.replace('\x92', utf8("'")[0].encode('latin1'))
    s = s.replace('\x93', utf8('"')[0].encode('latin1'))
    s = s.replace('\x94', utf8('"')[0].encode('latin1'))
    s = s.replace('\x95', utf8('-')[0].encode('latin1'))
    s = s.replace('\x96', utf8("à")[0].encode('latin1'))
    s = s.replace('\x97', utf8("-")[0].encode('latin1'))
    s = s.replace('\x99', utf8("tm")[0].encode('latin1'))
    s = s.replace('\xA3', utf8("¬")[0].encode('latin1'))
    s = s.replace('\xA4', utf8("¤")[0].encode('latin1'))
    s = s.replace('\xA7', utf8("§")[0].encode('latin1'))
    s = s.replace('\xC4', utf8("Ä")[0].encode('latin1'))
    s = s.replace('\xC5', utf8("Å")[0].encode('latin1'))
    s = s.replace('\xE4', utf8("ä")[0].encode('latin1'))
    s = s.replace('\xE5', utf8("å")[0].encode('latin1'))
    s = s.replace('\xE9', utf8("é")[0].encode('latin1'))
    s = s.replace('\xF6', utf8("ö")[0].encode('latin1'))
    #s = s.replace('\x95', '-')
    #s = s.replace('\x', "")
    #s = s.replace('\x', "")
    latin1 = codecs.getdecoder('latin1')
    s = latin1(s)[0].encode('utf8')
    if s == 'null':
        return None
    return s

def migrate_area_from_SKForum(db, thread_id, owner_id, name):
    print name
    cursor = db.cursor()
    thread = Thread(id=thread_id, owner_id=owner_id, name=fix_string(name), creation_time=datetime.now())
    thread.save()
    cursor.execute('select id, subject, body, user, timecreated, visible, parent, lastchanged, lastchangeduser from messages where area = '+unicode(thread_id)+' order by id')
    messages = cursor.fetchall()
    for data in messages:
        user = User.objects.get(pk=data[3])
        try:
            deleted_by = None
            if data[8] is not None:
                deleted_by = User.objects.get(pk=data[8])
        
            message = Message(
                id=data[0],
                body=fix_string(data[1]+'\n'+data[2]).rstrip(),
                owner=user,
                creation_time=data[4],
                deleted=not data[5],
                deleted_by=deleted_by,
                parent_message_id=data[6],
                parent_thread=thread)
            message.save()
        except:
            import codecs
            print 'threw away message id '+unicode(data[0])+' '+data[2]
            for c in data[2]:
                o = ord(c)
                if o >= 127:
                    print c+': '+hex(o)
                    
def get_cursor():
    import MySQLdb
    
    db = MySQLdb.connect('localhost', 'box', ';heLvN', 'forum')
    cursor = db.cursor()
    return cursor

def migrate_areas_from_SKForum(request = None):
    cursor = get_cursor()
    hex = codecs.getencoder('hex')
    latin1 = codecs.getdecoder('latin1')
    
    cursor.execute('select id, name from areas where id = 5 order by id')
    areas = cursor.fetchall()
    for data in areas:
        migrate_area_from_SKForum(db, data[0], 1, data[1])
   
    db.close()

def migrate_users_from_SKForum(request = None):
    #if not request.user.is_superuser:
        #raise Exception('super user specific action')

    cursor = get_cursor()
    hex = codecs.getencoder('hex')
    latin1 = codecs.getdecoder('latin1')

    everyone = get_everyone_group()

    cursor.execute('select id, name, password, realname, SecretEmail, PublicEmail, email, ICQ, telephone, mobilephone, address, other, birthdate from users where id != 1')
    users = cursor.fetchall()
    for user in users:
        u = User(
            id = user[0], 
            username = fix_string(user[1]), 
            email = user[4], 
            is_staff = False, 
            is_superuser = False)

        if u.email == None:
            u.email = user[5]
        if u.email == None:
            u.email = user[6]

        hexpassword = hex(base64.b64decode(user[2]))
        if hexpassword[1] > 18:
            u.password = "sha1$$" + hexpassword[0]
        else:    
            u.password = "invalid!"

        realname = user[3].rsplit(None, 1)
        if len(realname) >= 1:
            u.first_name = fix_string(realname[0])
        if u.first_name == None:
            u.first_name = ''
        if len(realname) >= 2:
            u.last_name = fix_string(realname[1])
        if u.last_name == None:
            u.last_name = ''

        u.save()

        # display name 1
        #d = Detail(name='display name', value=fix_string(user[1]), user=u)
        #d.save()

        def add_detail(object, name):
            if object != None and object != '' and object != 'null':
                d = Detail(name=name, value=fix_string(object), user=u)
                if d.value != None:
                    d.save()

        add_detail(user[5], 'public email')
        add_detail(user[6], 'protected email')
        add_detail(user[7], 'ICQ')
        add_detail(user[8], 'telephone')
        add_detail(user[9], 'mobilephone')
        add_detail(user[10], 'address')
        add_detail(user[11], 'other')

        # birthdate 12
        if user[12] != None and user[12] != '' and user[12] != 'null':
            m = MetaUser(user=u, birthday=user[12])
            m.save()

    db.close()