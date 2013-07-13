# Global django settings for curia project. 
# Specific local settings that should be different on different setups are in local_settings.py that you have to create yourself.

# set defaults
class LocalSettings:
    pass

local_settings = LocalSettings()
local_settings.DATABASE_ENGINE = 'sqlite3'
local_settings.DATABASE_NAME = '../curiadb'
local_settings.DATABASE_USER = ''
local_settings.DATABASE_PASSWORD  = ''
local_settings.ADMINS = ()
local_settings.ROOT_DIR = __file__.rsplit('/', 2)[0]
local_settings.EMAIL_USE_TLS = ''
local_settings.EMAIL_HOST = ''
local_settings.EMAIL_HOST_USER = ''
local_settings.EMAIL_HOST_PASSWORD = ''
local_settings.EMAIL_PORT = ''
local_settings.THREADED_FORUMS = False
local_settings.REGISTRATION_SYSTEM = 'invite'
local_settings.REGISTRATION_SYSTEM = 'invite'
local_settings.SECRET_KEY = 'PD4LqI9n7Eni2KXZMnYFrMgLTR2NZ4gDCUoNcthy'

SESSION_COOKIE_DOMAIN = '.kodare.net'

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = local_settings.ADMINS
MANAGERS = ADMINS

DATABASE_ENGINE = local_settings.DATABASE_ENGINE           # 'postgresql', 'mysql', 'sqlite3' or 'ado_mssql'.
DATABASE_NAME = local_settings.DATABASE_NAME             # Or path to database file if using sqlite3.
DATABASE_USER = local_settings.DATABASE_USER             # Not used with sqlite3.
DATABASE_PASSWORD = local_settings.DATABASE_PASSWORD         # Not used with sqlite3.

DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

# session settings
SESSION_COOKIE_AGE = 60 * 60 * 3 # Age of cookie, in seconds (3 hours).
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True

# Local time zone for this installation. All choices can be found here:
# http://www.postgresql.org/docs/current/static/datetime-keywords.html#DATETIME-TIMEZONE-SET-TABLE
TIME_ZONE = 'Europe/Stockholm'

# Language code for this installation. All choices can be found here:
# http://www.w3.org/TR/REC-html40/struct/dirlang.html#langcodes
# http://blogs.law.harvard.edu/tech/stories/storyReader$15
LANGUAGE_CODE = 'sv-se'
LANGUAGES = (('sv-se', 'Svenska'), ('sv', 'Svenska'))#, ('en', 'English'), ('en-us', 'English'))
DEFAULT_CHARSET = 'UTF-8'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = local_settings.ROOT_DIR+'/curia/site-media'

# URL that handles the media served from MEDIA_ROOT.
# Example: "http://media.lawrence.com"
MEDIA_URL = '/site-media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'rl8bc-2n(yulg+yce-=yru^#02iu_3)pk29ll9ufha(2wrww-$'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader'
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'curia.middleware.CuriaMiddleware',
    'curia.middleware.RequireLoginMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'curia.context_processors.site',
    'curia.context_processors.external',
    'curia.context_processors.domain',
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
)

SITE_ID=1

ROOT_URLCONF = 'curia.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    local_settings.ROOT_DIR+'/curia/templates',
)

LOGIN_URL = '/login/'

EMAIL_USE_TLS = local_settings.EMAIL_USE_TLS
EMAIL_HOST = local_settings.EMAIL_HOST 
EMAIL_HOST_USER = local_settings.EMAIL_HOST_USER
EMAIL_HOST_PASSWORD = local_settings.EMAIL_HOST_PASSWORD
EMAIL_PORT = local_settings.EMAIL_PORT

SERVER_EMAIL = 'robot@eldmyra.se'

IMAGE_SIZE = 800, 520
THUMBNAIL_SIZE = 110, 110
ICON_SIZE = THUMBNAIL_SIZE
USER_THUMBNAIL_SIZE = 60, 60
PICTURE_SIZE = 200, 200
LOGO_SIZE = PICTURE_SIZE

# IMAGE_SIZE = 800, 600
# THUMBNAIL_SIZE = 110, 110
# USER_THUMBNAIL_SIZE = THUMBNAIL_SIZE
# USER_ICON_SIZE = 60, 60
# USER_PICTURE_SIZE = 200, 200
# GROUP_PICTURE_SIZE = PICTURE_SIZE

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.flatpages',
    'sorl.thumbnail',
    'curia.base',
    'curia.authentication',
    'curia.labels',
    'curia.times',
    'curia.forums',
    'curia.documents',
    'curia.registration',
    'curia.images',
    'curia.files',
    'curia.notifications',
    'curia.calendars',
    'curia.messages',
    'curia.bugs',
    'curia.homepage',
    'curia.debts',
)

REGISTRATION_SYSTEM = local_settings.REGISTRATION_SYSTEM
THREADED_FORUMS = local_settings.THREADED_FORUMS

try:
    from local_settings import *
except ImportError:
    print 'no local_settings.py found, using defaults...'

