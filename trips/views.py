from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from network.graph_utils import bfs_path
from .models import Trip, TripNode
from .serializers import TripSerializer
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.shortcuts import redirect
from .forms import TripForm
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

def create_trip(request):
    if request.user.role != 'driver':
        messages.error(request, "Only drivers can create trips.")
        return redirect('trips:index')
    if request.method == 'POST':
        form = TripForm(request.POST)
        if form.is_valid():
            trip = form.save(commit=False)
            trip.created_by = request.user
            trip.save()
            
            route = bfs_path(trip.start_node, trip.end_node)
            TripNode.objects.bulk_create([
                TripNode(trip=trip, node=node, order=i)
                for i, node in enumerate(route)
            ])

            messages.success(request, "Trip created successfully!")
            return redirect('trips:index')
    else:
        form = TripForm()
    return render(request, 'trips/create_trip.html', {'form': form})
class BookTripView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, slug):
        if request.user.role != 'passenger':
            messages.error(request, "Only passengers can book trips.")
            return redirect('trips:index')
        trip = get_object_or_404(Trip, slug=slug)

        if request.user in trip.passengers.all():
            messages.warning(request, "You have already booked this trip.")
            return redirect('trips:index')
        
        if trip.created_by == request.user:
            messages.warning(request, "You cannot book your own trip.")
            return redirect('trips:index')
        if trip.passengers.count() >= trip.available_seats:
            messages.warning(request, "This trip is already fully booked.")
            return redirect('trips:index')

        trip.passengers.add(request.user)
        messages.success(request, "Trip booked successfully!")
        return redirect('trips:index')

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

    def get(self, request, slug):
        trip = get_object_or_404(Trip, slug=slug)
        route = TripNode.objects.filter(trip=trip).order_by('order')

        return Response({'trip': trip, 'route': route}, template_name='trips/trip_detail.html')