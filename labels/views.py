from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import *
from curia.shortcuts import *
from curia import *
from curia.labels.models import Label
from curia.labels import get_labels
from django.contrib.auth.models import User
from datetime import datetime
from sets import Set
from django.utils.translation import ugettext as _
from django.utils.encoding import smart_unicode
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Group
from curia.labels.models import SuggestedLabel
from django.utils.simplejson import dumps
import django.forms 

def add_suggested_label(request, group_id, cls):
    group = get_object_or_404_and_check_access(request, Group, pk=group_id, command='add')
    content_type = get_content_type(cls)

    class SuggestedLabelForm(django.forms.Form):
        title = django.forms.CharField(max_length=1024, label=_('New tab'), help_text=_('Items with this label will automatically appear in the tab.'))

    if request.POST:
        form = SuggestedLabelForm(request.POST)
        if form.is_valid():
            added_label = SuggestedLabel.objects.create(title=form.cleaned_data['title'], label=form.cleaned_data['title'], group=group, created_by=request.user, content_type=content_type)
            form = SuggestedLabelForm(initial={})
            labels = SuggestedLabel.objects.filter(group=group, content_type=content_type)
            return render_to_response(request, 'labels/add_suggested_label.html', {'added_label':added_label, 'form':form, 'labels':labels})
    else:
        labels = SuggestedLabel.objects.filter(group=group, content_type=content_type)
        form = SuggestedLabelForm(initial={})

    return render_to_response(request, 'labels/add_suggested_label.html', {'form':form, 'labels':labels})

def delete_suggested_label(request, group_id, label_id):
    group = get_object_or_404_and_check_access(request, Group, pk=group_id, command='delete')
    SuggestedLabel.objects.get(pk=label_id).delete()
    
    from django.core import serializers
    return HttpResponse(dumps(label_id, ensure_ascii=False), mimetype="text/json; charset=UTF-8")
