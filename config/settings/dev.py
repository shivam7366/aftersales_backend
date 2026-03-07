from .base import *

DEBUG = True

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@aftersales.com'

# Frontend URL for password reset link
FRONTEND_URL = 'http://localhost:3000/forgot-password'