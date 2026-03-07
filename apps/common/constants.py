
class RedisTTL:
    '''Constants for Redis cache keys and their time-to-live (TTL) values.'''
    USER_SESSION_TTL = 60 * 60 * 24  # 24 hours in seconds
    OTP_TTL = 5 * 60  # 5 minutes in seconds
    PASSWORD_RESET_TTL = 30 * 60  # 30 minutes in seconds
    OTP_RESEND_TTL =  60  # 1 minute in seconds
