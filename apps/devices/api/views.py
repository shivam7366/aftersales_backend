from rest_framework.viewsets import ViewSet
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .serializers import DeviceSerializer
from apps.devices.models import Device


class DeviceViewSet(ViewSet):
    '''View set for handling CRUD operations on devices registered by users.'''

    permission_classes = [IsAuthenticated]

    def get_object(self,uuid,user):
        '''Helper method to retrieve a device by its UUID and the authenticated user.'''
        try:
            return Device.objects.get(uuid=uuid,user=user)
        except Device.DoesNotExist:
            return None

    def list(self,request):
        '''List all devices registered by the authenticated user.'''
        devices=Device.objects.filter(user=request.user)
        serializer=DeviceSerializer(devices,many=True)
        return Response({'data':serializer.data,'message':'Devices retrieved successfully'},status=status.HTTP_200_OK)
    
   
    def create(self,request):
        '''Create a new device entry for the authenticated user.'''
        serializer=DeviceSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({'error':serializer.errors,'message':'Device creation failed.'},status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save(user=request.user)
        return Response({'data':serializer.data,'message':'Device created successfully.'},status=status.HTTP_201_CREATED)
    
    def retrieve(self,request,pk=None):
        ''' Retrieve a specific device by its UUID for the authenticated user.'''

        device=self.get_object(pk,request.user)
        if not device:
            return Response({'message':'Device not found.'},status=status.HTTP_404_NOT_FOUND)
        serializer=DeviceSerializer(device)
        return Response({'data':serializer.data,'message':'Device retrieved successfully.'},status=status.HTTP_200_OK)
    
    def partial_update(self,request,pk=None):
        device=self.get_object(pk,request.user)
        if not device:
            return Response({'message':'Device not found.'},status=status.HTTP_404_NOT_FOUND)
        
        serializer=DeviceSerializer(device,data=request.data,partial=True)
        if not serializer.is_valid():
            return Response({'error':serializer.errors,'message':'Device update failed.'},status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response({'data':serializer.data,'message':'Device updated successfully.'},status=status.HTTP_200_OK)
    
    def destroy(self,request,pk=None):
        device=self.get_object(pk,request.user)
        if not device:
            return Response({'message':'Device not found.'},status=status.HTTP_404_NOT_FOUND)
        device.delete()
        return Response({'message':'Device deleted successfully.'},status=status.HTTP_204_NO_CONTENT)

    