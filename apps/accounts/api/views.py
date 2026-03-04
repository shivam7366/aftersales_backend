from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer,LoginSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenError, InvalidToken
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.permissions import AllowAny  
from apps.accounts.models import User



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