from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.parsers import MultiPartParser,FormParser

from apps.common.permissions import IsCustomer, IsServiceProfessional, IsAdmin, IsAdminOrServiceProfessional,IsAdminOrCustomer
from apps.service_requests.services import VisitingChargeCalculatorService, ActivityLogService
from apps.service_requests.models import ServiceRequest, ServiceRequestDocument
from .serializers import (
    ServiceRequestCreateSerializer,
    ServiceRequestListSerializer,
    ServiceRequestDetailSerializer,
    ServiceRequestDocumentSerializer,
)


class ServiceRequestViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']

    from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, serializers
from apps.common.permissions import IsCustomer, IsServiceProfessional, IsAdmin, IsAdminOrServiceProfessional
from apps.service_requests.services import VisitingChargeCalculatorService, ActivityLogService
from apps.service_requests.models import ServiceRequest, ServiceRequestDocument
from .serializers import (
    ServiceRequestCreateSerializer,
    ServiceRequestListSerializer,
    ServiceRequestDetailSerializer,
    ServiceRequestDocumentSerializer,
)


class ServiceRequestViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_permissions(self):
        if self.action in ['list', 'retrieve',  'partial_update']:
            return [IsAuthenticated()]
        if self.action in [ 'create','destroy']:
            return [IsCustomer()]
        if self.action == 'assign':
            return [IsAdmin()]
        if self.action == 'send_quote':
            return [IsAdminOrServiceProfessional()]
        if self.action in ['approve_quote', 'close']:
            return [IsCustomer()]
        if self.action == 'resolve':
            return [IsServiceProfessional()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        role = self.request.auth.get('role') if self.request.auth else None

        if role == 'admin':
            return ServiceRequest.objects.select_related(
                'device', 'customer', 'assigned_to'
            ).prefetch_related('activities', 'documents').all()

        if role == 'service_professional':
            return ServiceRequest.objects.select_related(
                'device', 'customer', 'assigned_to'
            ).prefetch_related('activities', 'documents').filter(assigned_to=user)

        return ServiceRequest.objects.select_related(
            'device', 'customer', 'assigned_to'
        ).prefetch_related('activities', 'documents').filter(customer=user)

    def get_serializer_class(self):
        if self.action == 'create':
            return ServiceRequestCreateSerializer
        if self.action == 'list':
            return ServiceRequestListSerializer
        return ServiceRequestDetailSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        device = serializer.validated_data['device']
        service_type = serializer.validated_data['service_type']

        visit_charge = VisitingChargeCalculatorService.calculate_visiting_charge(
            service_type,
            device.purchase_date
        )

        initial_status = (
            ServiceRequest.StatusChoices.VISIT_CHARGE_PENDING
            if visit_charge > 0
            else ServiceRequest.StatusChoices.PENDING
        )

        instance = serializer.save(
            customer=self.request.user,
            visit_charge=visit_charge,
            total_charge=visit_charge,
            status=initial_status
        )

        ActivityLogService.log_activity(
            service_request=instance,
            user=self.request.user,
            from_status=None,
            to_status=initial_status,
            comment='Service request created.'
        )

    def perform_update(self, serializer):
        instance = self.get_object()

        allowed_statuses = [
            ServiceRequest.StatusChoices.PENDING,
            ServiceRequest.StatusChoices.VISIT_CHARGE_PENDING,
        ]
        if instance.status not in allowed_statuses:
            raise serializers.ValidationError(
                'Cannot update request at this stage.'
            )

        allowed_fields = {'preferred_visit_date', 'issue_description'}
        for key in self.request.data:
            if key not in allowed_fields:
                raise serializers.ValidationError(
                    f'You cannot update {key}.'
                )

        serializer.save()

        ActivityLogService.log_activity(
            service_request=instance,
            user=self.request.user,
            from_status=instance.status,
            to_status=instance.status,
            comment='Service request updated by customer.'
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.status not in [
            ServiceRequest.StatusChoices.PENDING,
            ServiceRequest.StatusChoices.VISIT_CHARGE_PENDING,
        ]:
            return Response(
                {'message': 'Cannot cancel request at this stage.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        old_status = instance.status
        instance.status = ServiceRequest.StatusChoices.REJECTED
        instance.save()

        ActivityLogService.log_activity(
            service_request=instance,
            user=request.user,
            from_status=old_status,
            to_status=ServiceRequest.StatusChoices.REJECTED,
            comment='Service request cancelled by customer.'
        )

        return Response(
            {'message': 'Service request cancelled successfully.'},
            status=status.HTTP_200_OK
        )

    # --- Admin Actions ---

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        instance = self.get_object()

        assignable_statuses = [
            ServiceRequest.StatusChoices.PENDING,
            ServiceRequest.StatusChoices.VISIT_CHARGE_PENDING,
            ServiceRequest.StatusChoices.VISIT_CHARGE_PAID,
        ]
        if instance.status not in assignable_statuses:
            return Response(
                {
                    'message': (
                        'Can only assign requests that are pending, awaiting visit '
                        'charge, or visit charge paid (not yet assigned).'
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        professional_uuid = request.data.get('professional_uuid')
        if not professional_uuid:
            return Response(
                {'message': 'professional_uuid is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from apps.accounts.models import User
        try:
            professional = User.objects.get(
                uuid=professional_uuid,
                role__name='service_professional'
            )
        except User.DoesNotExist:
            return Response(
                {'message': 'Service professional not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        old_status = instance.status
        instance.assigned_to = professional
        instance.status = ServiceRequest.StatusChoices.ASSIGNED
        instance.save()

        ActivityLogService.log_activity(
            service_request=instance,
            user=request.user,
            from_status=old_status,
            to_status=ServiceRequest.StatusChoices.ASSIGNED,
            comment=f'Assigned to {professional.first_name} {professional.last_name}.'
        )

        return Response(
            {
                'data': ServiceRequestDetailSerializer(instance).data,
                'message': 'Service request assigned successfully.'
            },
            status=status.HTTP_200_OK
        )

    # --- Professional Actions ---

    @action(detail=True, methods=['post'], url_path='send-quote')
    def send_quote(self, request, pk=None):
        instance = self.get_object()

        if instance.status != ServiceRequest.StatusChoices.IN_PROGRESS:
            return Response(
                {'message': 'Can only send quote for in-progress requests.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        parts_charge = request.data.get('parts_charge')
        if parts_charge is None:
            return Response(
                {'message': 'parts_charge is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            parts_charge = float(parts_charge)
            if parts_charge < 0:
                raise ValueError
        except (ValueError, TypeError):
            return Response(
                {'message': 'parts_charge must be a positive number.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        old_status = instance.status
        instance.parts_charge = parts_charge
        instance.total_charge = (instance.visit_charge or 0) + parts_charge
        instance.status = ServiceRequest.StatusChoices.QUOTE_SENT
        instance.save()

        ActivityLogService.log_activity(
            service_request=instance,
            user=request.user,
            from_status=old_status,
            to_status=ServiceRequest.StatusChoices.QUOTE_SENT,
            comment=f'Quote sent. Parts charge: {parts_charge}. Total: {instance.total_charge}.'
        )

        return Response(
            {
                'data': ServiceRequestDetailSerializer(instance).data,
                'message': 'Quote sent successfully.'
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='start-work')
    def start_work(self, request, pk=None):
        instance = self.get_object()

        if instance.status != ServiceRequest.StatusChoices.ASSIGNED:
            return Response(
            {'message': 'Can only start work on assigned requests.'},
            status=status.HTTP_400_BAD_REQUEST
            )

        old_status = instance.status
        instance.status = ServiceRequest.StatusChoices.IN_PROGRESS
        instance.save()

        ActivityLogService.log_activity(
        service_request=instance,
        user=request.user,
        from_status=old_status,
        to_status=ServiceRequest.StatusChoices.IN_PROGRESS,
        comment='Professional started working on the request.'
        )

        return Response(
        {'message': 'Service request is now in progress.'},
        status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        instance = self.get_object()

        if instance.status != ServiceRequest.StatusChoices.QUOTE_PAYMENT_PAID:
            return Response(
                {'message': 'Can only resolve after payment is completed.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        resolution_notes = request.data.get('resolution_notes')
        if not resolution_notes:
            return Response(
                {'message': 'resolution_notes is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        old_status = instance.status
        instance.resolution_notes = resolution_notes
        instance.status = ServiceRequest.StatusChoices.RESOLVED
        instance.save()

        ActivityLogService.log_activity(
            service_request=instance,
            user=request.user,
            from_status=old_status,
            to_status=ServiceRequest.StatusChoices.RESOLVED,
            comment=f'Resolved. Notes: {resolution_notes}'
        )

        return Response(
            {
                'data': ServiceRequestDetailSerializer(instance).data,
                'message': 'Service request resolved successfully.'
            },
            status=status.HTTP_200_OK
        )

    # --- Customer Actions ---

    @action(detail=True, methods=['post'], url_path='approve-quote')
    def approve_quote(self, request, pk=None):
        instance = self.get_object()

        if instance.status != ServiceRequest.StatusChoices.QUOTE_SENT:
            return Response(
                {'message': 'No quote to approve.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        old_status = instance.status
        instance.status = ServiceRequest.StatusChoices.QUOTE_APPROVED
        instance.save()

        ActivityLogService.log_activity(
            service_request=instance,
            user=request.user,
            from_status=old_status,
            to_status=ServiceRequest.StatusChoices.QUOTE_APPROVED,
            comment='Quote approved by customer.'
        )

        return Response(
            {
                'data': ServiceRequestDetailSerializer(instance).data,
                'message': 'Quote approved. Please proceed with payment.'
            },
            status=status.HTTP_200_OK
        )
        
    @action(detail=True, methods=['post'], url_path='reject-quote')
    def reject_quote(self, request, pk=None):
         instance = self.get_object()

         if instance.status != ServiceRequest.StatusChoices.QUOTE_SENT:
            return Response(
            {'message': 'No quote to reject.'},
            status=status.HTTP_400_BAD_REQUEST
        )

         reason = request.data.get('reason', '')

         old_status = instance.status
         instance.status = ServiceRequest.StatusChoices.REJECTED
         instance.save()

         ActivityLogService.log_activity(
        service_request=instance,
        user=request.user,
        from_status=old_status,
        to_status=ServiceRequest.StatusChoices.REJECTED,
        comment=f'Quote rejected by customer. Reason: {reason}' if reason else 'Quote rejected by customer.'
        )

         return Response(
        {'message': 'Quote rejected successfully.'},
        status=status.HTTP_200_OK
    )

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        instance = self.get_object()

        if instance.status != ServiceRequest.StatusChoices.RESOLVED:
            return Response(
                {'message': 'Can only close resolved requests.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        old_status = instance.status
        instance.status = ServiceRequest.StatusChoices.CLOSED
        instance.save()

        ActivityLogService.log_activity(
            service_request=instance,
            user=request.user,
            from_status=old_status,
            to_status=ServiceRequest.StatusChoices.CLOSED,
            comment='Service request closed by customer.'
        )

        return Response(
            {'message': 'Service request closed successfully.'},
            status=status.HTTP_200_OK
        )


class ServiceRequestDocumentViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'delete']
    pagination_class = None
    serializer_class = ServiceRequestDocumentSerializer
    parser_classes=[MultiPartParser,FormParser]

    def get_permissions(self):
        return [IsAuthenticated()]

    def get_queryset(self):
        return ServiceRequestDocument.objects.filter(
            service_request__uuid=self.kwargs['service_request_uuid'],
            service_request__customer=self.request.user
        ).order_by('-created_at')

    def perform_create(self, serializer):
        try:
            service_request = ServiceRequest.objects.get(
                uuid=self.kwargs['service_request_uuid'],
                # customer=self.request.user
            )
        except ServiceRequest.DoesNotExist:
            raise serializers.ValidationError('Service request not found.')

        allowed_statuses = [
            ServiceRequest.StatusChoices.PENDING,
            ServiceRequest.StatusChoices.VISIT_CHARGE_PENDING,
            ServiceRequest.StatusChoices.VISIT_CHARGE_PAID,
            ServiceRequest.StatusChoices.ASSIGNED,
            ServiceRequest.StatusChoices.IN_PROGRESS,
        ]
        if service_request.status not in allowed_statuses:
            raise serializers.ValidationError(
                'Cannot upload documents at this stage.'
            )

        serializer.save(service_request=service_request)