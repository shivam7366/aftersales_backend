

import uuid
import hashlib
from apps.common.services.redis_service import RedisService
from apps.common.constants import RedisTTL


class PasswordResetService: 
    ''' Service class for handling password reset functionality, including generating and validating password reset tokens.'''

    @staticmethod
    def _reset_token_cache_key(hashed_token):
        '''Generates a Redis cache key for storing password reset tokens based on the hashed token.'''
        return f'password_reset:{hashed_token}'
    
    @staticmethod
    def generate_reset_token():
        '''Generates a unique password reset token and returns the hashed token for storage.'''
        raw_token = str(uuid.uuid4())
        hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()
        print(f"Generated raw token: {raw_token}, hashed token: {hashed_token}")  # Debugging statement
        return raw_token, hashed_token
    
    @classmethod
    def store_reset_token(cls, hashed_token, email):
        '''Stores the hashed password reset token in Redis with an expiration time.'''
        RedisService.set(cls._reset_token_cache_key(hashed_token), email, ttl=RedisTTL.PASSWORD_RESET_TTL)

    @classmethod
    def validate_reset_token(cls, raw_token):
        '''Validates the provided raw token by hashing it and checking against the stored hashed token in Redis.'''

        hashed_token = hashlib.sha256(str(raw_token).encode()).hexdigest()
        print(f"Validating raw token: {raw_token}, hashed token: {hashed_token}")  # Debugging statement
        email = RedisService.get(cls._reset_token_cache_key(hashed_token))
        print(f"Retrieved email from Redis for hashed token: {email}")  # Debugging statement
        if email:
            RedisService.delete(cls._reset_token_cache_key(hashed_token))
            return True, email
        return False, None
    

    