from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import *
from curia.shortcuts import *
import django.forms
from curia.times.models import Time
from django.utils.translation import ugettext as _

def list_bookmarks(request):
    return render_to_response(request, 'times/index.html', {'times': Time.objects.filter(user=request.user.id, bookmark=True)})

def view_time(request, time_id):
    time = get_object_or_404(Time, pk=time_id)
    related = []
    for c in time._meta.get_all_related_many_to_many_objects():
        related_list = getattr(time, c.name+'_set').all()
        if related_list:
            related.append({'name':c.name, 'list':related_list})
    
    return render_to_response(request, 'times/time.html', {'time':time, 'related':related})
    
def view_category(request, time_id, category):
    time = get_object_or_404(Time, pk=time_id)
    try:
        related_list = getattr(time, category+'_set').all()
    except AttributeError:
        raise Http404

    return render_to_response(request, 'times/category.html', {'time':time, 'category':category, 'related_list':related_list})

def remove_bookmark(request):
    return set_bookmark_status(request, False)

def add_bookmark(request):
    return set_bookmark_status(request, True)

def set_bookmark_status(request, bookmark_status):
    content_type = ContentType.objects.get(app_label=request.GET['app_label'], model=request.GET['model'])
    id=request.GET['id']
    time = Time.objects.get(object_id=id, content_type=content_type.id)
    if time == None:
        Time(user=request.user, content_type=content_type, object_id=id)
    time.bookmark = bookmark_status
    time.save()
    return HttpResponseRedirect(time.get_content_object().get_absolute_url())