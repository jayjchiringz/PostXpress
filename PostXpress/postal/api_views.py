# postal/api_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from .jwt_auth import FarmFuzionJWTAuthentication
from .models import Parcel, ParcelEvent
from .serializers import ParcelSerializer, ParcelEventSerializer
import logging

logger = logging.getLogger(__name__)

class FarmerParcelListCreateView(generics.ListCreateAPIView):
    """
    API endpoint for FarmFuzion farmers to list and create parcels
    """
    authentication_classes = [FarmFuzionJWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ParcelSerializer
    
    def get_queryset(self):
        # Return parcels where farmer is either sender or receiver
        return Parcel.objects.filter(
            sender_email=self.request.user.email
        ) | Parcel.objects.filter(
            receiver_email=self.request.user.email
        )
    
    def perform_create(self, serializer):
        # Auto-assign served_by to the authenticated user
        serializer.save(
            served_by=self.request.user,
            sender_email=self.request.user.email,
            sender_name=self.request.user.get_full_name() or self.request.user.username
        )

class FarmerParcelDetailView(generics.RetrieveUpdateAPIView):
    """
    API endpoint for viewing and updating a specific parcel
    """
    authentication_classes = [FarmFuzionJWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ParcelSerializer
    lookup_field = 'tracking_number'
    
    def get_queryset(self):
        return Parcel.objects.filter(
            sender_email=self.request.user.email
        ) | Parcel.objects.filter(
            receiver_email=self.request.user.email
        )

class FarmerTrackParcelView(APIView):
    """
    API endpoint for tracking parcels with real-time location
    """
    authentication_classes = [FarmFuzionJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, tracking_number):
        try:
            parcel = Parcel.objects.get(tracking_number=tracking_number)
            
            # Ensure user has access to this parcel
            if parcel.sender_email != request.user.email and parcel.receiver_email != request.user.email:
                return Response(
                    {'error': 'Access denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Update location if needed
            parcel.update_location()
            
            events = ParcelEvent.objects.filter(parcel=parcel).order_by('-timestamp')
            
            return Response({
                'tracking_number': parcel.tracking_number,
                'status': parcel.status,
                'current_location': {
                    'latitude': float(parcel.current_latitude) if parcel.current_latitude else None,
                    'longitude': float(parcel.current_longitude) if parcel.current_longitude else None,
                },
                'origin': {
                    'station': parcel.origin_location.office if parcel.origin_location else None,
                    'latitude': float(parcel.origin_location.latitude) if parcel.origin_location else None,
                    'longitude': float(parcel.origin_location.longitude) if parcel.origin_location else None,
                },
                'destination': {
                    'station': parcel.destination.office if parcel.destination else None,
                    'latitude': float(parcel.destination.latitude) if parcel.destination else None,
                    'longitude': float(parcel.destination.longitude) if parcel.destination else None,
                },
                'events': ParcelEventSerializer(events, many=True).data,
                'estimated_delivery': parcel.updated_at + timedelta(days=3) if parcel.status != 'Delivered' else None,
            })
            
        except Parcel.DoesNotExist:
            return Response(
                {'error': 'Parcel not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

class LogisticsDashboardView(APIView):
    """
    API endpoint for farmer's logistics dashboard
    """
    authentication_classes = [FarmFuzionJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Get all parcels for this farmer
        parcels = Parcel.objects.filter(
            sender_email=request.user.email
        ) | Parcel.objects.filter(
            receiver_email=request.user.email
        )
        
        # Statistics
        stats = {
            'total_parcels': parcels.count(),
            'in_transit': parcels.filter(status='In Transit').count(),
            'delivered': parcels.filter(status='Delivered').count(),
            'pending_pickup': parcels.filter(status='Ready for dispatch').count(),
        }
        
        # Recent parcels
        recent_parcels = parcels.order_by('-created_at')[:10]
        
        return Response({
            'stats': stats,
            'recent_parcels': ParcelSerializer(recent_parcels, many=True).data,
        })
