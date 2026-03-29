from .base import *
import os

DEBUG = False 

ALLOWED_HOSTS = ['54.206.92.55', 'aftersales-staging-api.shivam-gupta.life']
DATABASES={
    'default':{
        'ENGINE':'django.db.backends.postgresql',
        'NAME': os.environ['DB_NAME'],
        'USER': os.environ['DB_USER'],
        'PASSWORD': os.environ['DB_PASSWORD'],
        'HOST': os.environ['DB_HOST'],
        'PORT': '5432',
        
    }

}



REDIS_URL = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/0')

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# AWS S3 Settings
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_BUCKET_NAME')
AWS_S3_REGION_NAME = 'ap-south-1'
AWS_DEFAULT_ACL = None  # private by default
AWS_S3_FILE_OVERWRITE = False  # don't overwrite files with same name
AWS_QUERYSTRING_EXPIRE = 3600





EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ['EMAIL_HOST']
EMAIL_PORT = 587
EMAIL_HOST_USER = os.environ['EMAIL_HOST_USER']
EMAIL_HOST_PASSWORD = os.environ['EMAIL_HOST_PASSWORD']
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = os.environ['EMAIL_HOST_USER']