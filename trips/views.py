from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from network.graph_utils import bfs_path
from .models import Trip, TripNode
from .serializers import TripSerializer
from django.shortcuts import render

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views import View
from rest_framework.renderers import TemplateHTMLRenderer


class IndexView(View):
    def get(self, request):
        return render(request, 'trips/index.html')


class TripViewSet(viewsets.ModelViewSet):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user

        if user.role != 'driver':
            raise PermissionDenied("Only drivers can create trips.")

        trip = serializer.save(created_by=user)

        route = bfs_path(trip.start_node, trip.end_node)

        TripNode.objects.bulk_create([
            TripNode(trip=trip, node=node, order=i)
            for i, node in enumerate(route)
        ])

class BookTripView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, name):
        if request.user.role != 'passenger':
            return Response({"error": "Only passengers allowed"}, status=403)

        try:
            trip = Trip.objects.get(name=name)
        except Trip.DoesNotExist:
            return Response({"error": "Trip not found"}, status=404)

        trip.passengers.add(request.user)

        return Response(TripSerializer(trip).data)

class ListTripsView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [TemplateHTMLRenderer]

    def get(self, request):
        trips = Trip.objects.all()
        return Response(
        {'trips': trips},
        template_name='trips/list_trips.html'
    )


class TripDetailView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [TemplateHTMLRenderer]

    def get(self, request, username):
        trips = Trip.objects.filter(created_by__username=username)
        route = TripNode.objects.filter(trip__created_by__username=username).order_by('order')

        return Response({'trips': trips, 'route': route}, template_name='trips/trip_detail.html')