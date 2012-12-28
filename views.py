from django.http import *

def echo_headers(request):
    return HttpResponse(unicode(request.META))
    
def test(request):
    asd()
    from curia.shortcuts import *
    from curia.files.models import File
    return render_to_response(request, 'test.html', {'obj':File.objects.get(pk=1)})
    
def index_html(request):
    return HttpResponseRedirect('/')
    
def autocomplete(request, key):
    from django.utils.simplejson import dumps
    if key == 'members':
        results = [unicode(x) for x in request.community.user_set.all()]
        return HttpResponse(dumps(results, ensure_ascii=False), mimetype="text/json; charset=UTF-8")
