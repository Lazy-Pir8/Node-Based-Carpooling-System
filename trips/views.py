from django.shortcuts import render
from .forms import TripForm
from .models import Trip
from django.contrib.auth import get_user_model
User = get_user_model()
from django.contrib.auth.decorators import login_required

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