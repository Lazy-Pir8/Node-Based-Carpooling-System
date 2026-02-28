from django.shortcuts import render
from .forms import TripForm
from .models import Trip
# Create your views here.

def index(request):
    return render(request, 'trips/index.html')


def add_trip(request):
    if request.method == 'POST':
        form = TripForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request, 'trips/index.html')
    else: 
        form = TripForm()
    return render(request, 'trips/add_trip.html', {"form": form})


def book_trip(request):
    trips = Trip.objects.all()
    return render(request, 'trips/book_trip.html', {
        "trips": trips
    })