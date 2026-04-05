from rest_framework import serializers
from apps.accounts.models import User,Role
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from apps.accounts.services import GoogleAuthService

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
    

class GoogleAuthSerializer(serializers.Serializer):
    token=serializers.CharField(required=True,write_only=True)

    def validate_token(self,value):
        try:
            google_user=GoogleAuthService.verify_google_token(value)
        except ValueError as e:
            raise serializers.ValidationError(str(e))
        self.context['google_user']=google_user
        return value
    
    def create_or_get_user(self):
        google_user=self.context['google_user']
        email=google_user['email']

        try:
            user=User.objects.select_related('role').get(email=email)

            if not user.google_id:
                user.google_id = google_user['google_id']
                user.email_verified=True
                user.save()

            return user,False
        except User.DoesNotExist:
            customer_role=Role.objects.get(name=Role.RoleChoices.CUSTOMER)

            user=User.objects.create(
                email=email,
                first_name=google_user['first_name'],
                last_name=google_user['last_name'],
                email_verified=True,
                google_id=google_user['google_id'],
                role=customer_role
            )
            return user,True
        

class VerifyOTPSerializer(serializers.Serializer):
    email=serializers.EmailField(required=True)
    otp=serializers.CharField(required=True,max_length=6,min_length=6)

    def validate_email(self,value):
        return value.lower()
    
    def validate_otp(self,value):
        if not value.isdigit():
            raise serializers.ValidationError('OTP must be numeric')
        return value

class ResendOTPSerializer(serializers.Serializer):
    email=serializers.EmailField(required=True)

    def validate_email(self,value):
        return value.lower()
    
class PasswordResetRequestSerializer(serializers.Serializer):
    email=serializers.EmailField(required=True)

    def validate_email(self,value):
        return value.lower()
    
class AdminCreateUserSerializer(serializers.Serializer):
    """Admin-only: create customer or service_professional accounts."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    phone_number = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=15
    )
    role = serializers.ChoiceField(choices=['customer', 'service_professional'])

    def validate_email(self, value):
        normalized = value.lower()
        if User.objects.filter(email=normalized).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return normalized

    def create(self, validated_data):
        role = Role.objects.get(name=validated_data.pop('role'))
        password = validated_data.pop('password')
        phone = validated_data.pop('phone_number', None)
        if phone == '':
            phone = None
        user = User.objects.create_user(
            email=validated_data['email'],
            password=password,
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone_number=phone,
            role=role,
        )
        user.email_verified = True
        user.save(update_fields=['email_verified'])
        return user

    def to_representation(self, instance):
        return {
            'uuid': str(instance.uuid),
            'email': instance.email,
            'first_name': instance.first_name,
            'last_name': instance.last_name,
            'phone_number': instance.phone_number,
            'role': instance.role.name if instance.role else None,
            'email_verified': instance.email_verified,
        }


class ResetPasswordSerializer(serializers.Serializer):
    token=serializers.CharField(required=True)
    new_password=serializers.CharField(required=True)
    confirm_password=serializers.CharField(required=True)

    def validate(self,attrs):
        if len(attrs['new_password'])<8:
            raise serializers.ValidationError({'message':'Password must be at least 8 characters long'})
        if attrs['new_password']!=attrs['confirm_password']:
            raise serializers.ValidationError({'message':'Passwords do not match'})
        
        return attrs
     

            

