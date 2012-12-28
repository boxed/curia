import os
import sys
sys.path.append('..')
os.environ['DJANGO_SETTINGS_MODULE'] = 'curia.settings'
import settings # Assumed to be in the same directory.

from django.db import connection
import keyword
from django.db import models

def get_table_name(model):
    return unicode(model._meta).replace('.', '_')

cursor = connection.cursor()
def table_info(connection, cursor, table_name):
    result = []
    try:
        relations = connection.introspection.get_relations(cursor, table_name)
    except NotImplementedError:
        relations = {}
    try:
        indexes = connection.introspection.get_indexes(cursor, table_name)
    except NotImplementedError:
        indexes = {}
    for i, row in enumerate(connection.introspection.get_table_description(cursor, table_name)):
        column_name = row[0]
        att_name = column_name.lower()
        extra_params = {}  # Holds Field parameters such as 'db_column'.

        if i in relations:
            rel_to = relations[i][1] == table_name and "'self'" or table2model(relations[i][1])
            field_type = 'ForeignKey(%s' % rel_to
            if att_name.endswith('_id'):
                att_name = att_name[:-3]
            else:
                extra_params['db_column'] = column_name
        else:
            field_type = connection.introspection.data_types_reverse[row[1]]
        
            # This is a hook for DATA_TYPES_REVERSE to return a tuple of
            # (field_type, extra_params_dict).
            if type(field_type) is tuple:
                field_type, new_params = field_type
                extra_params.update(new_params)

        # Don't output 'id = meta.AutoField(primary_key=True)', because
        # that's assumed if it doesn't exist.
        if att_name == 'id' and field_type == 'AutoField' and extra_params == {'primary_key': True}:
            continue

        # Add 'null' and 'blank', if the 'null_ok' flag was present in the
        # table description.
        if row[6]: # If it's NULL...
            extra_params['blank'] = True
            if not field_type in ('TextField', 'CharField'):
                extra_params['null'] = True
        if att_name == 'id':
            field_type = 'AutoField'
        if att_name.endswith('_id'):
            field_type = 'ForeignKey'
            att_name = att_name[:-3]
            
        if att_name == 'email':
            field_type = 'EmailField'

        # print '%s %s' % (att_name.ljust(20), field_type)
        result.append((str(att_name), str(field_type)))
    return result
        
# for table_name in connection.introspection.get_table_list(cursor):
#     if table2model(table_name) != 'AuthenticationMetauser':
#          continue
#     #print 'class %s(models.Model):' % table2model(table_name)
#     print table_name
#     table_info(cursor, table_name)
def remove_duplicates(foo, bar):
    r_foo = range(len(foo))
    r_foo.reverse()
    for foo_i in r_foo:
        if foo[foo_i] in bar:
            r_bar = range(len(bar))
            r_bar.reverse()
            for bar_i in r_bar:
                if bar[bar_i] == foo[foo_i]:
                    del bar[bar_i]
            del foo[foo_i]
    
for app in settings.INSTALLED_APPS:
    if not app.startswith('django.') and not app.startswith('sorl.'):
        module = __import__(app, fromlist=['models']).models
        for model_name in dir(module):
            model = getattr(module, model_name)
            if hasattr(model, '_meta'): # HACK: check if it really is a model
                if model.__name__ == 'ContentType':
                    continue
                fields_from_code = []
                field_creation = {}
                for field in model._meta.fields:
                    # print '%s %s' % (field.name.ljust(20), type(field).__name__)
                    field_type = str(type(field).__name__)
                    if field_type in ('ImageField', 'FileField'):
                        field_type = 'CharField'
                    if field_type == 'OneToOneField':
                        field_type = 'ForeignKey'
                    if field.name == 'object_id':
                        field.name = 'object'
                        field_type = 'ForeignKey'
                    key = (str(field.name), field_type)
                    fields_from_code.append(key)
                    field_creation[key] = ' '.join(connection.creation.sql_field(field, model))
                fields_from_db = table_info(connection, cursor, get_table_name(model))
                remove_duplicates(fields_from_db, fields_from_code)
                if len(fields_from_db) != 0 or len(fields_from_code) != 0:
                    print '**', model.__name__
                    if len(fields_from_db) != 0:
                        print 'deleted:'#,fields_from_db
                        for fieldname in fields_from_db:
                            print 'alter table %s drop column %s ' % (model._meta.db_table, fieldname)
                    if len(fields_from_code) != 0:
                        print 'added:'#,fields_from_code
                        for fieldname in fields_from_code:
                            #print field_creation
                            print 'alter table %s add column %s ' % (model._meta.db_table, field_creation[fieldname])
        #except AttributeError:
        #    print 'no models found for', app
