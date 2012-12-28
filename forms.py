# import django.forms
# from django.db import models
from django.utils.translation import ugettext as _
# 
# class FormFieldWrapper(django.forms.FormWrapper):
#     def __init__(self, formfield, data, error_list, manipulator):
#         self.formfield, self.data, self.error_list = formfield, data, error_list
#         self.field_name = self.formfield.field_name # for convenience in templates
#         self.manipulator = manipulator
#         
#     def __unicode__(self):
#         # TODO: add error list output!
#         from django.utils.text import capfirst
#         from django.db import models
#         opts = self.manipulator.opts
#         label_prefix = '<div class="form-row"><label for="' + self.formfield.get_id() + '"'
#         if self.formfield.is_required:
#             label_prefix += ' class="required"'
#         label_prefix += '>'
#         try:
#             field = opts.get_field(self.field_name)
#             label_prefix += capfirst(field.verbose_name)
#         except models.FieldDoesNotExist:
#             label_prefix += capfirst(self.field_name)
#             field = ''
#         
#         label_suffix = '</label> '
#         rendered_field = self.formfield.render(self.data)
#         error = ', '.join([unicode(i) for i in self.error_list])
#              
#         if isinstance(field, models.BooleanField):
#             return rendered_field + label_prefix+label_suffix+error+'</div>'
#         else:
#             return label_prefix + ':' + label_suffix + rendered_field+' '+error+'</div>'
#         
# class FormWrapper(django.forms.FormWrapper):
#     def __getitem__(self, key):
#         for field in self.manipulator.fields:
#             if field.field_name == key:
#                 if hasattr(field, 'requires_data_list') and hasattr(self.data, 'getlist'):
#                     data = self.data.getlist(field.field_name)
#                 else:
#                     data = self.data.get(field.field_name, None)
#                 if data is None:
#                     data = ''
#                 return FormFieldWrapper(field, data, self.error_dict.get(field.field_name, []), self.manipulator)
#         raise KeyError
# 
# # hack to remove seconds from time fields
import django.forms.fields as djfields

class TimeInput(djfields.TextInput):
    input_type = 'text' # Subclasses must define this.
    
    def render(self, name, value, attrs=None):
        if value is None: value = ''
        final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
        if value != '':
            # Only add the 'value' attribute if a value is non-empty.
            final_attrs['value'] = force_unicode(value)[0:-3]
        return mark_safe(u'<input%s />' % flatatt(final_attrs))

from django.forms.widgets import MultiWidget, TextInput
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.forms.util import flatatt
class SplitDateTimeWidget2(MultiWidget):
    """
    A Widget that splits datetime input into two <input type="text"> boxes.
    """
    def __init__(self, attrs=None):
        widgets = (TextInput(attrs={'class': 'vDateField'}), TimeInput(attrs=attrs))
        super(SplitDateTimeWidget2, self).__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return [value.date(), value.time().replace(microsecond=0)]
        return [None, None]
        
class SplitDateTimeField(djfields.MultiValueField):
    default_error_messages = {
        'invalid_date': _(u'Enter a valid date.'),
        'invalid_time': _(u'Enter a valid time.'),
    }

    def __init__(self, *args, **kwargs):
        from curia.widgets import *
        errors = self.default_error_messages.copy()
        if 'error_messages' in kwargs:
            errors.update(kwargs['error_messages'])
        fields = (
            djfields.DateField(error_messages={'invalid': errors['invalid_date']}),
            djfields.TimeField(error_messages={'invalid': errors['invalid_time']}),
        )
        self.widget = SplitDateTimeWidget2
        super(SplitDateTimeField, self).__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        if data_list:
            import datetime
            # Raise a validation error if time or date is empty
            # (possible if SplitDateTimeField has required=False).
            if data_list[0] in EMPTY_VALUES:
                raise ValidationError(self.error_messages['invalid_date'])
            if data_list[1] in EMPTY_VALUES:
                raise ValidationError(self.error_messages['invalid_time'])
            return datetime.datetime.combine(*data_list)
        return None
        


# import django.forms
# from django.django.forms.Forms import BoundField
# from django.template import Context, loader
# 
# class TemplatedForm(django.forms.Form):
#     def output_via_template(self):
#         "Helper function for fieldsting fields data from form."
#         bound_fields = [BoundField(self, field, name) for name, field in self.fields.items()]
#         c = Context(dict(form = self, bound_fields = bound_fields))
#         t = loader.get_template('form.html')
#         return t.render(c)
#     
#     def __unicode__(self):
#         return self.output_via_template()