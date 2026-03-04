from rest_framework import serializers
from apps.accounts.models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.CharField(source='role.name', read_only=True)

    class Meta:
        model = User
        fields = [
            'uuid',
            'email',
            'password',
            'first_name',
            'last_name',
            'phone_number',
            'role',
            'email_verified',
        ]
        extra_kwargs = {
            'first_name': {'required': True, 'allow_blank': False},
            'last_name': {'required': True, 'allow_blank': False},
            'uuid': {'read_only': True},
            'email_verified': {'read_only': True},
        }

    def validate_email(self, value):
        return value.lower()
    
    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        return value
    
    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            phone_number=validated_data.get('phone_number'),
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        return user
    
    # def to_representation(self, instance):
    #     user={
    #         'uuid': str(instance.uuid),
    #         'email': instance.email,
    #         'first_name': instance.first_name,
    #         'last_name': instance.last_name,
    #         'phone_number': instance.phone_number,
    #         'role': instance.role.name if instance.role else None,
    #         'email_verified': instance.email_verified,
    #     }
    #     return {
    #         'data': user,
    #         'message': 'Registration successful'
    #     }
    
class LoginSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role.name if user.role else None
        token['email_verified'] = user.email_verified
        return token

    def validate(self, attrs):
       data=super().validate(attrs)

    #    if not self.user.email_verified:
    #        raise serializers.ValidationError({'message':'Email is not verified'})
       data['user']={
           'uuid':str(self.user.uuid),
           'email':self.user.email,
           'first_name':self.user.first_name,
           'last_name':self.user.last_name,
           'phone_number':self.user.phone_number,
            'role':self.user.role.name if self.user.role else None,
            'email_verified':self.user.email_verified
           }
       data['message']='Login successful'
       return data
    

