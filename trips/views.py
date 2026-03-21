from django.shortcuts import render
from .forms import TripForm
from .models import Trip, TripNode
from django.contrib.auth import get_user_model
User = get_user_model()
from django.contrib.auth.decorators import login_required
from network.models import Node, Edge
from network.graph_utils import bfs_path
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import TripSerializer, TripNodeSerializer



# Create your views here.

def index(request):
    return render(request, 'trips/index.html')

@login_required
def add_trip(request):
    if request.method == 'POST':
        if request.user.role != 'driver':
            return render(request, 'trips/index.html', {"error": "Only drivers can add trips."})
        form = TripForm(request.POST)
        if form.is_valid():
            trip = form.save(commit=False)
            trip.created_by = request.user
            trip.save()

            start = trip.start_node
            end = trip.end_node
            
            route = bfs_path(start, end)

            for i, node in enumerate(route):
                TripNode.objects.create(trip=trip, node=node, order=i)
                

            return render(request, 'trips/index.html')
    else: 
        form = TripForm()
    return render(request, 'trips/add_trip.html', {"form": form})

@login_required
def book_trip(request):
    trips = Trip.objects.all()
    if request.user.role != 'passenger':
        return render(request, 'trips/index.html', {"error": "Only passengers can book trips."})
    return render(request, 'trips/book_trip.html', {
        "trips": trips
    })


def trip_detail(request, username):
    trip = Trip.objects.get(username=username)
    trip_nodes = TripNode.objects.filter(trip=trip).order_by('order')
    return render(request, 'trips/trip_detail.html', {
        "trip": trip,
        "trip_nodes": trip_nodes
    })
