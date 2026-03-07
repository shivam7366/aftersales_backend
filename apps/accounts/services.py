from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from django.conf import settings
from rest_framework import status


class GoogleAuthService:
    
    @staticmethod
    def verify_google_token(token):
        try:
            id_info = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID
            )
            if id_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Invalid token issuer')
            return {
                'email': id_info.get('email'),
                'first_name': id_info.get('given_name'),
                'last_name': id_info.get('family_name'),
                'email_verified': id_info.get('email_verified', False),
                'google_id' : id_info.get('sub')
            }
        except ValueError as e:
            # Token is invalid

            raise ValueError(f'Google token verification failed: {str(e)}')
            return None