from django.shortcuts import render
from django.shortcuts import redirect
from .forms import RegisterForm
from django.contrib.auth import authenticate, login
from django.contrib.auth import get_user_model
User = get_user_model()
from django.contrib.auth.views import LoginView, LogoutView
from trips.models import Trip
from trips.models import TripNode
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import UserSerializer
from django.views import View
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth import get_user_model
User = get_user_model()


# Create your views here.

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect('trips:index')
    else:
        form = LoginForm()

    return render(request, 'users/login.html', {'form': form})

class CustomLoginView(LoginView):
    template_name = 'users/login.html'

class RegisterView(View):
    def get(self, request):
        form = RegisterForm()
        return render(request, 'users/register.html', {'form': form})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.set_password(form.cleaned_data['password'])
            user.save()
            return redirect('trips:index')
        return render(request, 'users/register.html', {'form': form})

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        
        if form.is_valid():
            user = form.save()
            user.set_password(form.cleaned_data['password'])
            user.save()

            return redirect('trips:index')
    else:
        form = RegisterForm()
    
    return render(request, 'users/register.html', {'form': form})



def driver_dashboard(request, username):
    user = User.objects.filter(username=username).first()
    if not user or user.role != 'driver':
        messages.error(request, "Driver not found.")
        return redirect('trips:index')
    trips = Trip.objects.filter(created_by=user)
  
    return render(request, 'users/driver_dashboard.html',{
    "profile_user": user, 
    "trips": trips
    })

def passenger_dashboard(request):
    if request.user.role != 'passenger':
        messages.error(request, "Only passengers can access the dashboard.")
        return redirect('trips:index')
    trips = request.user.booked_trips.all()
  
    return render(request, 'users/passenger_dashboard.html',{
    "profile_user": request.user, 
    "trips": trips
    })

def dashboard_redirect(request, username):
    user = User.objects.filter(username=username).first()
    if not request.user.is_authenticated:
        return redirect('users:login')
    if request.user.role == 'driver' or user.role == 'driver':
        return redirect('users:driver_dashboard' , username=user.username)
    elif request.user.role == 'passenger':
        return redirect('users:passenger_dashboard')
    else:
        messages.error(request, "Invalid user role.")
        return redirect('trips:index')