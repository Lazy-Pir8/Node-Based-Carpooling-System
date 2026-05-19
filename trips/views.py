from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import now
from django.views import View
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from network.graph_utils import bfs_path
from network.models import Node
from .forms import TripForm
from .models import CarpoolRequest, DriverOffer, Trip, TripNode


class IndexView(View):
    def get(self, request):
        return render(request, "trips/index.html")


def _trip_route_nodes(trip):
    return list(TripNode.objects.filter(trip=trip).order_by("order"))


def compute_current_node(trip):
    nodes = _trip_route_nodes(trip)
    if not nodes:
        return None

    current_time = now()
    if trip.arrival_time and current_time >= trip.arrival_time:
        return nodes[-1].node

    if (
        trip.departure_time
        and trip.arrival_time
        and trip.departure_time <= current_time < trip.arrival_time
    ):
        elapsed = (current_time - trip.departure_time).total_seconds()
        total_duration = (trip.arrival_time - trip.departure_time).total_seconds()
        if total_duration <= 0:
            return nodes[0].node
        time_per_node = total_duration / max(len(nodes), 1)
        current_index = min(int(elapsed / max(time_per_node, 1)), len(nodes) - 1)
        return nodes[current_index].node

    return nodes[0].node


def create_trip(request):
    if not request.user.is_authenticated or request.user.role != "driver":
        messages.error(request, "Only drivers can create trips.")
        return redirect("trips:index")

    if request.method == "POST":
        form = TripForm(request.POST)
        if form.is_valid():
            trip = form.save(commit=False)
            trip.created_by = request.user
            trip.current_node = trip.start_node
            trip.save()

            route = bfs_path(trip.start_node, trip.end_node)
            if not route:
                trip.delete()
                messages.error(request, "No valid route found between selected nodes.")
                return redirect("trips:create_trip")

            TripNode.objects.bulk_create(
                [
                    TripNode(trip=trip, node=node, order=index)
                    for index, node in enumerate(route)
                ]
            )
            messages.success(request, "Trip created successfully!")
            return redirect("trips:index")
    else:
        form = TripForm()

    return render(request, "trips/create_trip.html", {"form": form})


class BookTripView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        if request.user.role != "passenger":
            messages.error(request, "Only passengers can book trips.")
            return redirect("trips:index")

        trip = get_object_or_404(Trip, slug=slug)
        if request.user in trip.passengers.all():
            messages.warning(request, "You have already booked this trip.")
            return redirect("trips:index")
        if trip.created_by == request.user:
            messages.warning(request, "You cannot book your own trip.")
            return redirect("trips:index")
        if trip.passengers.count() >= trip.available_seats:
            messages.warning(request, "This trip is already fully booked.")
            return redirect("trips:index")

        trip.passengers.add(request.user)
        messages.success(request, "Trip booked successfully!")
        return redirect("trips:index")


class ListTripsView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [TemplateHTMLRenderer]

    def get(self, request):
        trips = Trip.objects.all().order_by("departure_time")
        return Response({"trips": trips}, template_name="trips/list_trips.html")


class TripDetailView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [TemplateHTMLRenderer]

    def get(self, request, slug):
        trip = get_object_or_404(Trip, slug=slug)
        route = TripNode.objects.filter(trip=trip).order_by("order")
        current_node = compute_current_node(trip)
        return Response(
            {"trip": trip, "route": route, "current_node": current_node},
            template_name="trips/trip_detail.html",
        )


def is_within_n_nodes(route_nodes, target_node, max_distance=2):
    for route_node in route_nodes:
        path = bfs_path(route_node.node, target_node)
        if path and len(path) - 1 <= max_distance:
            return True
    return False


@login_required
def create_request(request):
    if request.user.role != "passenger":
        messages.error(request, "Only passengers can create requests.")
        return redirect("trips:index")

    if request.method == "POST":
        pickup = request.POST.get("pickup")
        destination = request.POST.get("destination")
        if not pickup or not destination or pickup == destination:
            messages.error(
                request, "Pickup and destination must be valid and different."
            )
            return redirect("trips:create_request")

        CarpoolRequest.objects.create(
            passenger=request.user,
            pickup_node_id=pickup,
            destination_node_id=destination,
        )
        return redirect("users:passenger_dashboard")

    nodes = Node.objects.all()
    return render(request, "trips/create_request.html", {"nodes": nodes})


@login_required
def request_offers(request, request_id):
    req = get_object_or_404(CarpoolRequest, id=request_id, passenger=request.user)
    return render(
        request, "trips/offers.html", {"request": req, "offers": req.offers.all()}
    )


@login_required
@transaction.atomic
def accept_offer(request, offer_id):
    offer = get_object_or_404(DriverOffer, id=offer_id)
    if offer.request.passenger_id != request.user.id:
        messages.error(request, "You cannot accept this offer.")
        return redirect("users:passenger_dashboard")

    if offer.request.status == "accepted":
        messages.warning(request, "Offer already accepted.")
        return redirect("users:passenger_dashboard")
    if offer.trip.passengers.count() >= offer.trip.available_seats:
        messages.error(request, "Trip is full.")
        return redirect("users:passenger_dashboard")

    offer.is_selected = True
    offer.save(update_fields=["is_selected"])
    offer.request.status = "accepted"
    offer.request.save(update_fields=["status"])
    offer.trip.passengers.add(offer.request.passenger)
    offer.request.offers.exclude(id=offer.id).delete()
    return redirect("users:passenger_dashboard")


@login_required
def cancel_offer(request, request_id):
    req = get_object_or_404(CarpoolRequest, id=request_id, passenger=request.user)
    req.status = "cancelled"
    req.save(update_fields=["status"])
    req.offers.all().delete()
    return redirect("users:passenger_dashboard")


@login_required
def driver_offers(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id, created_by=request.user)
    route_nodes = TripNode.objects.filter(trip=trip).order_by("order")

    valid_requests = []
    for req in CarpoolRequest.objects.filter(status="pending"):
        pickup_ok = is_within_n_nodes(route_nodes, req.pickup_node)
        destination_ok = is_within_n_nodes(route_nodes, req.destination_node)
        if pickup_ok and destination_ok:
            req.has_offered = req.offers.filter(driver=request.user).exists()
            valid_requests.append(req)

    return render(
        request,
        "trips/driver_requests.html",
        {"trip": trip, "requests": valid_requests},
    )


@login_required
def create_offer(request, request_id, trip_id):
    req = get_object_or_404(CarpoolRequest, id=request_id)
    trip = get_object_or_404(Trip, id=trip_id, created_by=request.user)

    if DriverOffer.objects.filter(request=req, driver=request.user).exists():
        messages.warning(request, "You already offered for this request.")
        return redirect("trips:driver_requests", trip_id=trip.id)

    # use remaining route for active trips
    current = trip.current_node or trip.start_node
    base_remaining = bfs_path(current, trip.end_node)
    path1 = bfs_path(current, req.pickup_node)
    path2 = bfs_path(req.pickup_node, req.destination_node)
    path3 = bfs_path(req.destination_node, trip.end_node)

    if not base_remaining or not path1 or not path2 or not path3:
        messages.error(request, "Cannot compute route.")
        return redirect("trips:driver_requests", trip_id=trip.id)

    new_path = path1 + path2[1:] + path3[1:]
    detour = max(0, len(new_path) - len(base_remaining))

    DriverOffer.objects.create(
        request=req,
        driver=request.user,
        trip=trip,
        fare=Decimal(trip.ticket_price),
        detour_distance=float(detour),
        detour=detour,
    )
    return redirect("trips:driver_requests", trip_id=trip.id)


class UpdateTripNodeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, trip_id):
        trip = get_object_or_404(Trip, id=trip_id, created_by=request.user)
        node_id = request.data.get("node_id")
        node = get_object_or_404(Node, id=node_id)

        trip_nodes = TripNode.objects.filter(trip=trip).order_by("order")
        target = trip_nodes.filter(node=node).first()
        if not target:
            return Response(
                {"detail": "Node is not in this trip route."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if trip.current_node:
            current = trip_nodes.filter(node=trip.current_node).first()
            if current and target.order < current.order:
                return Response(
                    {"detail": "Cannot move trip backwards."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        trip.current_node = node
        trip.started = True
        if node == trip.end_node:
            trip.completed = True
        trip.save(update_fields=["current_node", "started", "completed"])

        trip_nodes.filter(order__lte=target.order).update(is_passed=True)
        return Response(
            {"detail": "Trip node updated.", "current_node": node.name},
            status=status.HTTP_200_OK,
        )
