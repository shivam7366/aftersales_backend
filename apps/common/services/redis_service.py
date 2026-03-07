import redis
from django.conf import settings

class RedisService:

    '''Service class to interact with Redis for caching and other operations.'''
    
    _client=None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            cls._client=redis.Redis.from_url(settings.REDIS_URL)
        return cls._client
    
    @classmethod
    def set(cls,key,value,ttl=None):
        client=cls.get_client()
        client.set(key,value,ex=ttl)


    @classmethod
    def get(cls,key):
        client=cls.get_client()
        value=client.get(key)
        return value.decode('utf-8') if value else None
    
    @classmethod
    def delete(cls,key):
        client=cls.get_client()
        client.delete(key)
    
    @classmethod
    def exists(cls,key):
        client=cls.get_client()
        return client.exists(key)
    