from django.shortcuts import render
from django.shortcuts import redirect
from .forms import RegisterForm
from django.contrib.auth import authenticate, login
from django.contrib.auth import get_user_model
User = get_user_model()
from django.contrib.auth.views import LoginView, LogoutView
from trips.models import Trip
from trips.models import TripNode

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


def profile_view(request, username):
    user = User.objects.get(username=username)
    trips = Trip.objects.filter(created_by__username=username)

    return render(request, 'users/profile_driver.html', {"profile_user": user, "trips": trips,})