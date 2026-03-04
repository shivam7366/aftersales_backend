from django.urls import path, include
from .views import RegisterView,LoginView,CustomTokenRefreshView
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/',LoginView.as_view(),name='login'),
    path('token/refresh/',CustomTokenRefreshView.as_view(),name='token_refresh'),
]