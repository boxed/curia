ROOT_DIR = '/Users/boxed/Projects'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '../curiadb'
    }
}

ADMINS = (('Anders', 'boxed@killingar.net',),)

EMAIL_USE_TLS = False
EMAIL_HOST = 'outbound.mailhop.org'
EMAIL_HOST_USER = 'boxed'
EMAIL_HOST_PASSWORD = ';heLvN'
EMAIL_PORT = 2525

THREADED_FORUMS = True

SECRET_KEY = 'rl8bc-2n(yulg+yce-=yru^#02iu_3)pk29ll9ufha(2wrww-$'
