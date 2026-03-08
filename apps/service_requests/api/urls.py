from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import ServiceRequestViewSet, ServiceRequestDocumentViewSet

router = DefaultRouter()
router.register('', ServiceRequestViewSet, basename='service-request')

urlpatterns = [
    *router.urls,
    path(
        '<uuid:service_request_uuid>/documents/',
        ServiceRequestDocumentViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='service-request-documents'
    ),
    path(
        '<uuid:service_request_uuid>/documents/<uuid:pk>/',
        ServiceRequestDocumentViewSet.as_view({'delete': 'destroy'}),
        name='service-request-document-detail'
    ),
]