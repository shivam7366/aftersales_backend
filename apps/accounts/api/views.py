from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenError, InvalidToken
from rest_framework_simplejwt.tokens import AccessToken,RefreshToken
from rest_framework.permissions import AllowAny  

from django.conf import settings
from .serializers import RegisterSerializer,LoginSerializer,GoogleAuthSerializer,VerifyOTPSerializer,ResendOTPSerializer,ResetPasswordSerializer,PasswordResetRequestSerializer
from apps.accounts.models import User
from apps.common.services.otp_service import OTPService
from apps.common.services.password_reset_service import PasswordResetService
from apps.common.services.email_service import EmailService
from apps.common.permissions import IsAdmin



class RegisterView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'data':serializer.data,'message':'Registration Successfull.'}, status=status.HTTP_201_CREATED)
        return Response({'error':serializer.errors,'message':'Registration Failed'}, status=status.HTTP_400_BAD_REQUEST)
    

class LoginView(TokenObtainPairView):
     permission_classes = [AllowAny]
     serializer_class = LoginSerializer
   

class CustomTokenRefreshView(TokenRefreshView):

    permission_classes = [AllowAny]
     

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        # New access token
        access_token = AccessToken(serializer.validated_data['access'])

        # Fetch user from DB using uuid in token
        try:
            user = User.objects.select_related('role').get(
                uuid=access_token['uuid']
            )
            # Add custom claims to new access token
            access_token['role'] = user.role.name if user.role else None
            access_token['email_verified'] = user.email_verified
        except User.DoesNotExist:
            pass

        return Response(
            {
                'access': str(access_token),
                'message': 'Token refreshed successfully.'
            },
            status=status.HTTP_200_OK
        )



class GoogleAuthView(APIView):
    permission_classes=[AllowAny]
    authentication_classes=[]

    def post(self,request):
        serializer=GoogleAuthSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({'error':serializer.errors,'message':'Google authentication failed'},status=status.HTTP_400_BAD_REQUEST)
        
        user,is_new_user=serializer.create_or_get_user()

        refresh=RefreshToken.for_user(user)
        refresh['role']=user.role.name if user.role else None
        refresh['email_verified']=user.email_verified

        access_token=refresh.access_token
        access_token['role']=user.role.name if user.role else None
        access_token['email_verified']=user.email_verified

        return Response(
    {
        'data': {
            'access': str(access_token),
            'refresh': str(refresh),
            'user': {
                'uuid': str(user.uuid),
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone_number': user.phone_number,
                'role': user.role.name if user.role else None,
                'email_verified': user.email_verified
            },
            'is_new_user': is_new_user,
        },
        'message': 'Login successful.' if not is_new_user else 'Account created successfully.'
    },
    status=status.HTTP_200_OK
)
    
class VerifyOTPView(APIView):
    permission_classes=[AllowAny]
    authentication_classes=[]

    def post(self,request):
       serializer=VerifyOTPSerializer(data=request.data)
       if not serializer.is_valid():
           return Response({'error':serializer.errors,'message':'OTP verification failed'},status=status.HTTP_400_BAD_REQUEST)
       
       email=serializer.validated_data['email']
       otp=serializer.validated_data['otp']

       is_valid,message=OTPService.verify_otp(email,otp)

       if not is_valid:
           return Response({'message':message,},status=status.HTTP_400_BAD_REQUEST)
       
       # Mark user's email as verified
       try:
           user=User.objects.get(email=email)
           user.email_verified=True
           user.save()

       except User.DoesNotExist:
           return Response({'message':'User not found'},status=status.HTTP_404_NOT_FOUND)
       
           
       return Response({'message':message},status=status.HTTP_200_OK)
    
class ResendOTPView(APIView):
     permission_classes=[AllowAny]
     authentication_classes=[]

     def post(self,request):
         serializer=ResendOTPSerializer(data=request.data)

         if not serializer.is_valid():
             return Response({'error':serializer.errors,'message':'OTP resend failed'},status=status.HTTP_400_BAD_REQUEST)
         
         email=serializer.validated_data['email']

         try:
            user=User.objects.get(email=email)
         except User.DoesNotExist:
             return Response({'message':'User not found'},status=status.HTTP_404_NOT_FOUND)
         
         if user.email_verified:
             return Response({'message':'Email is already verified'},status=status.HTTP_400_BAD_REQUEST)
        

         if not OTPService.can_resend_otp(email):
             return Response({'message':'You can only resend OTP once every minute. Please try again later.'},status=status.HTTP_429_TOO_MANY_REQUESTS)
         
         success,message=OTPService.send_otp(email)

         if not success:
                return Response({'message':message},status=status.HTTP_400_BAD_REQUEST)
         
         return Response({'message':'OTP resent successfully'},status=status.HTTP_200_OK)
     

class PasswordResetRequestView(APIView):
    permission_classes=[AllowAny]
    authentication_classes=[]

    def post(self,request):
        serializer=PasswordResetRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({'error':serializer.errors,'message':'Password reset request failed'},status=status.HTTP_400_BAD_REQUEST)
        
        email=serializer.validated_data['email']

        try:
            user=User.objects.get(email=email)
            raw_token,hashed_token=PasswordResetService.generate_reset_token()
            PasswordResetService.store_reset_token(hashed_token,email)
            reset_link=f"{settings.FRONTEND_URL}?token={raw_token}"
            print(f"Password reset link for {email}: {reset_link}")  # Log the reset link for testing purposes
            success=EmailService.send_password_reset_email(email,reset_link)

            if not success:
                return Response({'message':'Failed to send password reset email. Please try again later.'},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            

        except User.DoesNotExist:
           pass

        return Response({'message':'If an account with that email exists, a password reset link has been sent.'},status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    permission_classes=[AllowAny]
    authentication_classes=[]

    def post(self,request):
        serializer=ResetPasswordSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({'error':serializer.errors,'message':'Password reset failed'},status=status.HTTP_400_BAD_REQUEST)
        
        token=serializer.validated_data['token']
        new_password=serializer.validated_data['new_password']

        is_valid,email=PasswordResetService.validate_reset_token(token)

        if not is_valid:
            return Response({'message':'Reset link is invalid or expired.'},status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user=User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            return Response({'message':'Password reset successful.'},status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'message':'User not found'},status=status.HTTP_404_NOT_FOUND)
   
   

class GetAllUsers(APIView):  
    permission_classes = [IsAdmin]

    def get(self, request):
        role = request.query_params.get('role')

        users = User.objects.select_related('role').all()

        if role:
            users = users.filter(role__name=role)

        data = [
            {
                'uuid': str(user.uuid),
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone_number': user.phone_number,
                'role': user.role.name if user.role else None,
                'email_verified': user.email_verified
            }
            for user in users
        ]

        return Response(
            {'data': data, 'message': 'Users retrieved successfully.'},
            status=status.HTTP_200_OK
        )
        