
import random
from apps.common.constants import RedisTTL
from apps.common.services.redis_service import RedisService
from apps.common.services.email_service import EmailService

class OTPService:
    '''Service class to generate, store, and validate One-Time Passwords (OTPs) for user authentication and verification processes.'''

    @staticmethod
    def generate_otp(length=6):
        '''Generates a random numeric OTP of the specified length.'''
        return ''.join(random.choices('0123456789', k=length))
    
    @staticmethod
    def _otp_cache_key(email):
        '''Generates a Redis cache key for storing OTPs based on the user's email.'''
        return f'otp:{email}'
    
    @staticmethod
    def _otp_attempt_cache_key(email):
        '''Generates a Redis cache key for tracking OTP verification attempts based on the user's email.'''
        return f'otp_attempts:{email}'
    
    @staticmethod
    def _otp_resend_cache_key(email):
        '''Generates a Redis cache key for tracking OTP resend attempts based on the user's email.'''
        return f'otp_resend_cooldown:{email}'


    @classmethod
    def verify_otp(cls,email,otp):
        '''Validates the provided OTP against the stored OTP in Redis for the given email.'''
        stored_otp = RedisService.get(cls._otp_cache_key(email))
        
        if stored_otp is None:

            return False, 'OTP has expired or does not exist'
        
        if stored_otp != otp:

            # Increment OTP attempt count
            attempt_key = cls._otp_attempt_cache_key(email)
            attempts = RedisService.get(attempt_key)
            attempts = int(attempts) + 1 if attempts else 1
            RedisService.set(attempt_key, attempts, ttl=RedisTTL.OTP_TTL)

            if attempts >= 5:
                RedisService.delete(cls._otp_cache_key(email))
                RedisService.delete(attempt_key)
                return False, 'Too many failed attempts. OTP has been invalidated.'
            
            return False, 'Invalid OTP'
        
        # OTP is valid, reset attempt count and delete OTP
        RedisService.delete(cls._otp_cache_key(email))
        RedisService.delete(cls._otp_attempt_cache_key(email))
        return True, 'OTP verified successfully'
    
    @classmethod
    def can_resend_otp(self,email):
        '''Checks if the user can resend an OTP based on the cooldown period.'''
        return not RedisService.exists(self._otp_resend_cache_key(email))
    
    @classmethod
    def send_otp(self,email):
        '''Generates and stores a new OTP in Redis for the given email, and sets a cooldown for resending OTPs.'''
        if not self.can_resend_otp(email):
            return False, 'OTP resend is on cooldown. Please wait before requesting a new OTP.'
        
        otp = self.generate_otp()
        RedisService.set(self._otp_cache_key(email), otp, ttl=RedisTTL.OTP_TTL)
        RedisService.set(self._otp_resend_cache_key(email), '1', ttl=RedisTTL.OTP_RESEND_TTL)
        
        EmailService.send_otp_email(email=email,otp=otp)
        return True, 'OTP sent successfully'
    