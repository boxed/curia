To set up curia create a file called "local_settings.py" containing the following:

ROOT_DIR = '/the/path/to/where/curia/is/not/including/curia'
                             
DATABASE_ENGINE = 'postgresql' # valid alternatives are postgresql, mysql and sqlite3
DATABASE_NAME = 'curia'         
DATABASE_USER = 'postgres'      
DATABASE_PASSWORD = ''