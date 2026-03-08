from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import DeviceViewSet

router=DefaultRouter()
router.register(r'',DeviceViewSet,basename='device')

urlpatterns=router.urls