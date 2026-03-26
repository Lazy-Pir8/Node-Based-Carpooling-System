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
from .models import CarpoolRequest, DriverOffer
from network.models import Node
from django.contrib.auth.decorators import login_required
from django.db.models import Count


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

def is_within_n_nodes(route_nodes, target_node, max_distance=2):
    for route_node in route_nodes:
        path = bfs_path(route_node.node, target_node)
        if path and len(path) -1 <= max_distance:
            return True
    return False

@login_required
def create_request(request):
    if request.user.role != 'passenger':
        messages.error(request, "Only passengers can create requests.")
        return redirect('trips:index')
    if request.method == "POST":
        pickup = request.POST['pickup']
        dest = request.POST['destination']

        CarpoolRequest.objects.create(
            passenger=request.user,
            pickup_node_id=pickup,
            destination_node_id=dest
        )


        return redirect('users:passenger_dashboard')

    nodes = Node.objects.all()
    return render(request, "trips/create_request.html", {"nodes": nodes})




@login_required
def request_offers(request, request_id):
    req = CarpoolRequest.objects.get(id=request_id, passenger=request.user)

    return render(request, "trips/offers.html", {
        "request": req,
        "offers": req.offers.all()
    })


@login_required
def accept_offer(request, offer_id):
    offer = DriverOffer.objects.get(id=offer_id)

    if offer.request.status == 'accepted':
        messages.warning(request, "Offer already accepted.")
        return redirect('users:passenger_dashboard')

    if offer.trip.passengers.count() >= offer.trip.available_seats:
        messages.error(request, "Trip is full.")
        return redirect('users:passenger_dashboard')
   
    offer.is_selected = True
    offer.save()

    offer.request.status = 'accepted'
    offer.request.save()
    

    offer.trip.passengers.add(offer.request.passenger)
    offer.request.offers.exclude(id=offer.id).delete()
    return redirect('users:passenger_dashboard')


@login_required
def cancel_offer(request, request_id):
    req = get_object_or_404(CarpoolRequest, id=request_id, passenger=request.user)

    req.status = 'cancelled'
    req.save()

    req.offers.all().delete()   

    return redirect('users:passenger_dashboard')

@login_required
def driver_offers(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id, created_by=request.user)

    all_requests = CarpoolRequest.objects.filter(status='pending')
    valid_requests = []
    route_nodes = TripNode.objects.filter(trip=trip).order_by('order')
    for req in all_requests:
        pickup_ok = is_within_n_nodes(route_nodes, req.pickup_node)
        dest_ok = is_within_n_nodes(route_nodes, req.destination_node)

        if pickup_ok and dest_ok:
            req.has_offered = req.offers.filter(driver=request.user).exists()
            valid_requests.append(req)

    return render(request, "trips/driver_requests.html", {
        "trip": trip,
        "requests": valid_requests,
        
    })

def driver_accept_offer(request, offer_id):
    offer = DriverOffer.objects.get(id=offer_id, driver=request.user)

    if offer.request.status == 'accepted':
        messages.warning(request, "Offer already accepted.")
        return redirect('users:driver_dashboard', username=request.user.username)

    if offer.trip.passengers.count() >= offer.trip.available_seats:
        messages.error(request, "Trip is full.")
        return redirect('users:driver_dashboard', username=request.user.username)
   
    offer.is_selected = True
    offer.save()

    offer.request.status = 'accepted'
    offer.request.save()
    
    offer.trip.passengers.add(offer.request.passenger)
    offer.request.offers.exclude(id=offer.id).delete()
    return redirect('users:driver_dashboard', username=request.user.username)

@login_required
def create_offer(request, request_id, trip_id):
    req = get_object_or_404(CarpoolRequest, id=request_id)
    trip = get_object_or_404(Trip, id=trip_id, created_by=request.user)

    if DriverOffer.objects.filter(request=req, driver=request.user).exists():
        messages.warning(request, "You already offered for this request.")
        return redirect('trips:driver_requests', trip_id=trip.id)

    path1 = bfs_path(trip.start_node, req.pickup_node)
    path2 = bfs_path(req.pickup_node, req.destination_node)
    path3 = bfs_path(req.destination_node, trip.end_node)

    if not path1 or not path2 or not path3:
        messages.error(request, "Cannot compute route.")
        return redirect('trips:driver_requests', trip_id=trip.id)

    new_path = path1 + path2[1:] + path3[1:]
    original_path = bfs_path(trip.start_node, trip.end_node)

    detour = len(new_path) - len(original_path)

    DriverOffer.objects.create(
        request=req,
        driver=request.user,
        trip=trip,
        fare=trip.ticket_price,
        detour_distance=detour
    )

    return redirect('trips:driver_requests', trip_id=trip.id)
