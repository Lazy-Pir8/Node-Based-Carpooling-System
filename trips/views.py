import decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.views import View

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.renderers import TemplateHTMLRenderer

from network.graph_utils import bfs_path, nodes_within_distance
from network.models import Node
from .models import Trip, TripNode, CarpoolRequest, DriverOffer, CarpoolServiceStatus
from .serializers import TripSerializer
from .forms import TripForm


# ────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────

def _service_enabled(request):
    """Returns True if the carpool service is active, else redirects with error."""
    if not CarpoolServiceStatus.get_solo().is_active:
        messages.error(request, "The carpool service is currently suspended.")
        return False
    return True


def _compute_fare(trip, passenger_pickup, passenger_dest):
    """
    Compute fare per task spec:
        fare = p * Σ(1/nᵢ) + base_fee
    where p = ticket_price (unit cost per hop) and nᵢ = passengers in car at hop i.

    We estimate nᵢ = current confirmed passengers + 1 (the new passenger).
    For simplicity we treat all hops from pickup→dest as having the same occupancy.
    """
    BASE_FEE = decimal.Decimal("5.00")
    p = trip.ticket_price if trip.ticket_price else decimal.Decimal("10.00")

    path = bfs_path(passenger_pickup, passenger_dest)
    hops = max(len(path) - 1, 0)

    # passengers already in car at time of service
    n_current = trip.passengers.count() + 1  # +1 for the new passenger
    if n_current == 0:
        n_current = 1

    fare = p * sum(decimal.Decimal(1) / decimal.Decimal(n_current) for _ in range(hops)) + BASE_FEE
    return round(fare, 2)


def _compute_detour(trip, pickup_node, dest_node):
    """Return extra nodes vs original remaining route after inserting pickup+dest."""
    remaining = list(
        TripNode.objects.filter(trip=trip, is_passed=False).order_by('order').values_list('node', flat=True)
    )
    if not remaining:
        return 0

    from network.models import Node as N
    current = trip.current_node or trip.start_node
    orig_end = trip.end_node

    orig_path = bfs_path(current, orig_end)
    orig_len = len(orig_path)

    # new route: current → pickup → dest → orig_end
    p1 = bfs_path(current, pickup_node)
    p2 = bfs_path(pickup_node, dest_node)
    p3 = bfs_path(dest_node, orig_end)

    if not p1 or not p2 or not p3:
        return None  # impossible route

    new_len = len(p1) + len(p2[1:]) + len(p3[1:])
    return max(new_len - orig_len, 0)


# ────────────────────────────────────────────────
# Basic pages
# ────────────────────────────────────────────────

class IndexView(View):
    def get(self, request):
        return render(request, 'trips/index.html')


# ────────────────────────────────────────────────
# Trip management (drivers)
# ────────────────────────────────────────────────

@login_required
def create_trip(request):
    if request.user.role != 'driver':
        messages.error(request, "Only drivers can create trips.")
        return redirect('trips:index')

    if request.method == 'POST':
        form = TripForm(request.POST)
        if form.is_valid():
            trip = form.save(commit=False)
            trip.created_by = request.user

            # Validate route exists
            route = bfs_path(trip.start_node, trip.end_node)
            if not route:
                messages.error(request, "No route found between the selected nodes.")
                return render(request, 'trips/create_trip.html', {'form': form})

            trip.current_node = trip.start_node
            trip.save()

            TripNode.objects.bulk_create([
                TripNode(trip=trip, node=node, order=i)
                for i, node in enumerate(route)
            ])

            messages.success(request, "Trip created successfully!")
            return redirect('users:driver_dashboard', username=request.user.username)
    else:
        form = TripForm()

    return render(request, 'trips/create_trip.html', {'form': form})


@login_required
def cancel_trip(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id, created_by=request.user)
    if trip.status != 'scheduled':
        messages.error(request, "Only scheduled trips can be cancelled.")
        return redirect('users:driver_dashboard', username=request.user.username)
    trip.status = 'cancelled'
    trip.save()
    messages.success(request, "Trip cancelled.")
    return redirect('users:driver_dashboard', username=request.user.username)


# ────────────────────────────────────────────────
# DRF API: update current node (driver reports position)
# ────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_current_node(request, trip_id):
    """
    POST /trips/api/trip/<trip_id>/update_node/
    Body: { "node_id": <int> }

    Driver reports they have reached a new node.
    """
    trip = get_object_or_404(Trip, id=trip_id, created_by=request.user)

    if trip.status not in ('scheduled', 'active'):
        return Response({'error': 'Trip is not active.'}, status=status.HTTP_400_BAD_REQUEST)

    node_id = request.data.get('node_id')
    if not node_id:
        return Response({'error': 'node_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

    node = get_object_or_404(Node, id=node_id)

    # Verify node is on the trip's route
    trip_node = TripNode.objects.filter(trip=trip, node=node).first()
    if not trip_node:
        return Response({'error': 'Node is not on this trip\'s route.'}, status=status.HTTP_400_BAD_REQUEST)

    # Mark all previous nodes as passed
    TripNode.objects.filter(trip=trip, order__lte=trip_node.order).update(is_passed=True)

    trip.current_node = node
    if trip.status == 'scheduled':
        trip.status = 'active'

    # If last node, complete the trip
    last_node = TripNode.objects.filter(trip=trip).order_by('-order').first()
    if last_node and last_node.node == node:
        trip.status = 'completed'

    trip.save()
    return Response({
        'message': f'Current node updated to {node.name}.',
        'status': trip.status,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_trip_status(request, trip_id):
    """
    GET /trips/api/trip/<trip_id>/status/
    Returns current node and status for real-time display.
    """
    trip = get_object_or_404(Trip, id=trip_id)
    route = list(TripNode.objects.filter(trip=trip).order_by('order').values(
        'order', 'node__id', 'node__name', 'is_passed'
    ))
    return Response({
        'trip_id': trip.id,
        'status': trip.status,
        'current_node': {
            'id': trip.current_node.id,
            'name': trip.current_node.name,
        } if trip.current_node else None,
        'route': route,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_carpool_requests_api(request, trip_id):
    """
    GET /trips/api/trip/<trip_id>/requests/
    Returns valid carpool requests for driver's trip (SSR helper).
    """
    trip = get_object_or_404(Trip, id=trip_id, created_by=request.user)
    route_nodes = list(TripNode.objects.filter(trip=trip, is_passed=False).order_by('order').select_related('node'))

    # Build set of reachable nodes within 2 hops of remaining route
    reachable = set()
    for tn in route_nodes:
        reachable.update(nodes_within_distance(tn.node, max_distance=2))

    valid_requests = []
    for req in CarpoolRequest.objects.filter(status='pending').select_related('passenger', 'pickup_node', 'destination_node'):
        if req.pickup_node in reachable and req.destination_node in reachable:
            detour = _compute_detour(trip, req.pickup_node, req.destination_node)
            fare = _compute_fare(trip, req.pickup_node, req.destination_node)
            valid_requests.append({
                'id': req.id,
                'passenger': req.passenger.username,
                'pickup_node': req.pickup_node.name,
                'destination_node': req.destination_node.name,
                'detour_nodes': detour,
                'fare': str(fare),
                'already_offered': req.offers.filter(driver=request.user).exists(),
            })

    return Response({'requests': valid_requests})


# ────────────────────────────────────────────────
# Trip listing & detail
# ────────────────────────────────────────────────

class ListTripsView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [TemplateHTMLRenderer]

    def get(self, request):
        trips = Trip.objects.exclude(status='cancelled').select_related('start_node', 'end_node', 'created_by', 'current_node')
        return Response({'trips': trips}, template_name='trips/list_trips.html')


class TripDetailView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [TemplateHTMLRenderer]

    def get(self, request, slug):
        trip = get_object_or_404(Trip, slug=slug)
        route = TripNode.objects.filter(trip=trip).order_by('order').select_related('node')
        return Response(
            {'trip': trip, 'route': route, 'current_node': trip.current_node},
            template_name='trips/trip_detail.html'
        )


# ────────────────────────────────────────────────
# Carpool requests (passengers)
# ────────────────────────────────────────────────

@login_required
def create_request(request):
    if request.user.role != 'passenger':
        messages.error(request, "Only passengers can create carpool requests.")
        return redirect('trips:index')

    if not _service_enabled(request):
        return redirect('trips:index')

    if request.method == "POST":
        pickup_id = request.POST.get('pickup')
        dest_id = request.POST.get('destination')

        if not pickup_id or not dest_id:
            messages.error(request, "Please select both pickup and destination nodes.")
        elif pickup_id == dest_id:
            messages.error(request, "Pickup and destination cannot be the same.")
        else:
            pickup = get_object_or_404(Node, id=pickup_id)
            dest = get_object_or_404(Node, id=dest_id)

            # Check route is possible
            if not bfs_path(pickup, dest):
                messages.error(request, "No path exists between the selected nodes.")
            else:
                CarpoolRequest.objects.create(
                    passenger=request.user,
                    pickup_node=pickup,
                    destination_node=dest,
                )
                messages.success(request, "Carpool request submitted!")
                return redirect('users:passenger_dashboard')

    nodes = Node.objects.all()
    return render(request, "trips/create_request.html", {"nodes": nodes})


@login_required
def request_offers(request, request_id):
    req = get_object_or_404(CarpoolRequest, id=request_id, passenger=request.user)
    return render(request, "trips/offers.html", {
        "carpool_request": req,
        "offers": req.offers.select_related('driver', 'trip').all(),
    })


@login_required
def accept_offer(request, offer_id):
    """Passenger accepts a driver's offer."""
    offer = get_object_or_404(DriverOffer, id=offer_id, request__passenger=request.user)

    if offer.request.status == 'accepted':
        messages.warning(request, "You already accepted an offer for this request.")
        return redirect('users:passenger_dashboard')

    if offer.trip.passengers.count() >= offer.trip.available_seats:
        messages.error(request, "Trip is full. Cannot accept this offer.")
        return redirect('users:passenger_dashboard')

    offer.is_selected = True
    offer.save()

    offer.request.status = 'accepted'
    offer.request.save()

    offer.trip.passengers.add(offer.request.passenger)
    # Remove other offers for this request
    offer.request.offers.exclude(id=offer.id).delete()

    messages.success(request, "Offer accepted! You are now on the trip.")
    return redirect('users:passenger_dashboard')


@login_required
def cancel_request(request, request_id):
    """Passenger cancels their pending carpool request."""
    req = get_object_or_404(CarpoolRequest, id=request_id, passenger=request.user)

    if req.status == 'accepted':
        messages.error(request, "Cannot cancel an already accepted request.")
        return redirect('users:passenger_dashboard')

    req.status = 'cancelled'
    req.save()
    req.offers.all().delete()

    messages.success(request, "Carpool request cancelled.")
    return redirect('users:passenger_dashboard')


# ────────────────────────────────────────────────
# Carpool requests (drivers)
# ────────────────────────────────────────────────

@login_required
def driver_requests_view(request, trip_id):
    """SSR page showing valid carpool requests for the driver's trip."""
    trip = get_object_or_404(Trip, id=trip_id, created_by=request.user)
    route_nodes = list(TripNode.objects.filter(trip=trip, is_passed=False).order_by('order').select_related('node'))

    reachable = set()
    for tn in route_nodes:
        reachable.update(nodes_within_distance(tn.node, max_distance=2))

    valid_requests = []
    for req in CarpoolRequest.objects.filter(status='pending').select_related('passenger', 'pickup_node', 'destination_node'):
        if req.pickup_node in reachable and req.destination_node in reachable:
            detour = _compute_detour(trip, req.pickup_node, req.destination_node)
            fare = _compute_fare(trip, req.pickup_node, req.destination_node)
            req.computed_detour = detour
            req.computed_fare = fare
            req.has_offered = req.offers.filter(driver=request.user).exists()
            valid_requests.append(req)

    return render(request, "trips/driver_requests.html", {
        "trip": trip,
        "requests": valid_requests,
    })


@login_required
def create_offer(request, request_id, trip_id):
    """Driver creates an offer for a passenger's carpool request."""
    if request.user.role != 'driver':
        messages.error(request, "Only drivers can make offers.")
        return redirect('trips:index')

    req = get_object_or_404(CarpoolRequest, id=request_id, status='pending')
    trip = get_object_or_404(Trip, id=trip_id, created_by=request.user)

    if DriverOffer.objects.filter(request=req, driver=request.user).exists():
        messages.warning(request, "You already submitted an offer for this request.")
        return redirect('trips:driver_requests', trip_id=trip.id)

    detour = _compute_detour(trip, req.pickup_node, req.destination_node)
    if detour is None:
        messages.error(request, "Cannot compute a valid route for this request.")
        return redirect('trips:driver_requests', trip_id=trip.id)

    fare = _compute_fare(trip, req.pickup_node, req.destination_node)

    DriverOffer.objects.create(
        request=req,
        driver=request.user,
        trip=trip,
        detour=detour,
        fare=fare,
    )
    messages.success(request, f"Offer submitted! Detour: {detour} nodes, Fare: ₹{fare}")
    return redirect('trips:driver_requests', trip_id=trip.id)


@login_required
def driver_accept_offer(request, offer_id):
    """Driver accepts a passenger's offer (identical effect to passenger accepting)."""
    offer = get_object_or_404(DriverOffer, id=offer_id, driver=request.user)

    if offer.request.status == 'accepted':
        messages.warning(request, "This offer is already accepted.")
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

    messages.success(request, "Carpool accepted!")
    return redirect('users:driver_dashboard', username=request.user.username)
