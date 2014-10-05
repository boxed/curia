from django import template
from curia import *
from django.db import connection
from django.utils.translation import ugettext as _
import django.forms
from datetime import datetime
from curia.forums.models import Thread
from curia.files.models import File
from curia.labels.models import Label

def add_patterns(urlpatterns, cls, prefix=''):
    from django.conf.urls import patterns
    urlpatterns += patterns('curia.labels.views',
        (r'^'+prefix+r'(?P<group_id>\d+)/add_suggested_label/$', 'add_suggested_label', {'cls': cls}),
        (r'^'+prefix+r'(?P<group_id>\d+)/delete_suggested_label/(?P<label>.*)/$', 'delete_suggested_label', {'cls': cls}),
    )

class LabelResult:
    def __init__(self, name, weight):
        self.name = name
        self.weight = weight
    
    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.__unicode__()

def get_labels(obj=None, cls=None, owner=None):
    from django.contrib.auth.models import User, Group
    if obj != None:
        from curia.labels.models import Label
        return [LabelResult(l.name, 1) for l in Label.objects.filter(content_type=get_content_type(obj), object_id=obj.id, deleted=False).order_by('id')]
    
    content_type = get_content_type(cls)

    cursor = connection.cursor()
    if content_type != None:    
        if owner != None and isinstance(owner, User):
            cursor.execute("SELECT name, COUNT(name) FROM labels_label WHERE content_type_id = %s AND owner_user_id = %s AND owner_group_id is Null AND deleted = 0 GROUP BY name", [content_type.id, owner.id])
        elif owner != None and isinstance(owner, Group):
            cursor.execute("SELECT name, COUNT(name) FROM labels_label WHERE content_type_id = %s AND owner_group_id = %s AND deleted = 0 GROUP BY name", [content_type.id, owner.id])
        else:
            cursor.execute("SELECT name, COUNT(name) FROM labels_label WHERE content_type_id = %s GROUP BY name", [content_type_id])
    else:    
        cursor.execute("SELECT name, COUNT(name) FROM labels_label GROUP BY name")

    return [LabelResult(x[0], x[1]) for x in cursor.fetchall()]

def get_objects_with_label(label, cls=None, owner=None):
    from django.contrib.auth.models import User, Group
    from curia.labels.models import Label
    content_type = get_content_type(cls)
     
    if isinstance(owner, User):
        labels = get_objects_from(Label, content_type=content_type, deleted=False, owner_user=owner, owner_group=None, name=label)
    elif isinstance(owner, Group):
        labels = get_objects_from(Label, content_type=content_type, deleted=False, owner_group=owner, name=label)
    else:
        labels = get_objects_from(Label, content_type=content_type, deleted=False, name=label)
        
    return [get_content_object(l) for l in labels]
    
def handle_labels(request, object, owner_group=None):
    from curia.labels.models import Label
    class EditForm(django.forms.Form):
        labels = django.forms.CharField(required=False, widget = django.forms.Textarea, label=_('Labels'))

    if request.POST:
        form = EditForm(request.POST)

        if form.is_valid():
            from curia import CaseInsentiveString
            new_labels = set([CaseInsentiveString(x.strip()) for x in form.cleaned_data['labels'].split(',')])
            old_labels = set([CaseInsentiveString(label) for label in get_labels(object)])

            added_labels = new_labels.difference(old_labels)
            removed_labels = old_labels.difference(new_labels)

            for label in removed_labels:
                if label != '':
                    temp_label = Label.objects.get(object_id=object.id,deleted=False,name=label,content_type=get_content_type(object))
                    temp_label.deleted = True
                    temp_label.deleted_by = request.user
                    temp_label.deletion_time = datetime.now()
                    temp_label.save()      

            for label in added_labels:
                if label != '':
                    label = label[0:1].capitalize()+label[1:]
                    Label.objects.create(object_id=object.id, deleted=False, name=label, content_type=get_content_type(object), created_by = request.user, owner_user=request.user, owner_group=owner_group)

def mark_labels_as_deleted(obj, user):
    labels = Label.objects.filter(content_type=get_content_type(obj), object_id=obj.id, deleted=False)
    for label in labels:
        label.deleted = True
        label.deleted_by = user
        label.deletion_time = datetime.now()
        label.save()

def search_objects_from(search, cls, owner_group):
    labels = []
    split_labels = [x.strip() for x in search.split(',')]
    split_labels = [x for x in split_labels if x != '']
    if len(split_labels) != 0:
        for split_label in split_labels:
            labels.extend(map(lambda x: x.strip(), split_label.split(' ')))
        if cls == Thread:
            name_or_title = 'name'
        else:
            name_or_title = 'title'
        
        content_type = get_content_type(cls)
        matches = []
        params = []
        table_name = cls._meta.db_table
        for label in labels:
            if cls == File:
                matches.append('('+table_name+'.'+name_or_title+' LIKE %s OR '+table_name+'.description LIKE %s OR '+table_name+'.id IN (SELECT labels_label.object_id FROM labels_label WHERE labels_label.name LIKE %s AND labels_label.content_type_id = %s AND labels_label.deleted = %s))')
                params.append('%'+label+'%')
            else:
                matches.append('('+table_name+'.'+name_or_title+' LIKE %s OR '+table_name+'.id IN (SELECT labels_label.object_id FROM labels_label WHERE labels_label.name LIKE %s AND labels_label.content_type_id = %s AND labels_label.deleted = %s))')
            params.append('%'+label+'%')
            params.append('%'+label+'%')
            params.append(content_type.id)
            params.append(False)
        params.append(False)
        params.append(owner_group.id)
        return cls.objects.extra(where=[' AND '.join(matches)+' AND '+table_name+'.deleted = %s AND '+table_name+'.owner_group_id = %s'], tables=['labels_label'], params=params ).distinct()
    else:
        return get_objects_from(cls, deleted=False, owner_group=owner_group)
