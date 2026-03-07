from django.urls import path, include
from .views import RegisterView,LoginView,CustomTokenRefreshView,GoogleAuthView,VerifyOTPView,ResendOTPView,PasswordResetRequestView,ResetPasswordView
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/',LoginView.as_view(),name='login'),
    path('token/refresh/',CustomTokenRefreshView.as_view(),name='token_refresh'),
    path('google-auth/',GoogleAuthView.as_view(),name='google_auth'),
    path('verify-otp/',VerifyOTPView.as_view(),name='verify_otp'),
    path('resend-otp/',ResendOTPView.as_view(),name='resend_otp'),
    path('password-reset-request/',PasswordResetRequestView.as_view(),name='password_reset_request'),
    path('reset-password/',ResetPasswordView.as_view(),name='reset_password'),

]