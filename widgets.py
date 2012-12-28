from django.forms import widgets
from django.utils.safestring import mark_safe
from django.forms.util import flatatt
from django.utils.encoding import force_unicode
from django.conf import settings
import django.forms

class CheckboxInput(widgets.CheckboxInput):
    def __init__(self, attrs=None, check_test=bool):
        super(CheckboxInput, self).__init__(attrs)
        # check_test is a callable that takes a value and returns True
        # if the checkbox should be checked for that value.
        self.check_test = check_test

    def render(self, name, value, attrs=None):
        final_attrs = self.build_attrs(attrs, type='checkbox', name=name)
        try:
            result = self.check_test(value)
        except: # Silently catch exceptions
            result = False
        if result:
            final_attrs['checked'] = 'checked'
        if value not in ('', True, False, None):
            # Only add the 'value' attribute if a value is non-empty.
            final_attrs['value'] = force_unicode(value)
        return mark_safe(u'<input%s /> <label for="id_%s">%s</label>' % (flatatt(final_attrs), name, self.attrs['label']))

    def value_from_datadict(self, data, files, name):
        if name not in data:
            # A missing value means False because HTML form submission does not
            # send results for unselected checkboxes.
            return False
        return super(CheckboxInput, self).value_from_datadict(data, files, name)
        
class DateTimeInput(widgets.DateTimeInput):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs',{}).update({'class': 'vDateField'})
        super(DateTimeInput, self).__init__(*args, **kwargs)
        
class DateWidget(widgets.TextInput):
    class Media:
        js = (settings.ADMIN_MEDIA_PREFIX + "js/calendar.js",
              settings.ADMIN_MEDIA_PREFIX + "js/admin/DateTimeShortcuts.js")

    def __init__(self, attrs={}):
        super(DateWidget, self).__init__(attrs={'class': 'vDateField', 'size': '10'})

class TimeWidget(widgets.TextInput):
    class Media:
        js = (settings.ADMIN_MEDIA_PREFIX + "js/calendar.js",
              settings.ADMIN_MEDIA_PREFIX + "js/admin/DateTimeShortcuts.js")

    def __init__(self, attrs={}):
        super(TimeWidget, self).__init__(attrs={'class': 'vTimeField', 'size': '8'})
