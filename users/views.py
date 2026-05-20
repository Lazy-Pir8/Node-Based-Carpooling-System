from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.decorators import login_required
from django.views import View

from trips.models import Trip, CarpoolRequest
from .forms import RegisterForm

User = get_user_model()


# ────────────────────────────────────────────────
# Auth
# ────────────────────────────────────────────────

class RegisterView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('trips:index')
        form = RegisterForm()
        return render(request, 'users/register.html', {'form': form})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            # Send to onboarding if role not set via form
            if not user.role:
                return redirect('users:onboarding')
            return redirect('trips:index')
        return render(request, 'users/register.html', {'form': form})


# ────────────────────────────────────────────────
# Onboarding (role selection — also used after Google OAuth)
# ────────────────────────────────────────────────

@login_required
def onboarding(request):
    # Skip if user already has a role (e.g. page refresh)
    if request.user.role and request.method == 'GET':
        return redirect('trips:index')

    if request.method == 'POST':
        role = request.POST.get('role')
        if role not in ('passenger', 'driver'):
            messages.error(request, "Please choose a valid role.")
            return render(request, 'users/onboarding.html')

        user = request.user
        user.role = role
        # Set a sensible username if it's still the default Google one
        username = request.POST.get('username', '').strip()
        if username and username != user.username:
            if User.objects.filter(username=username).exclude(pk=user.pk).exists():
                messages.error(request, "That username is already taken.")
                return render(request, 'users/onboarding.html')
            user.username = username
        user.save()
        messages.success(request, f"Welcome, {user.username}! You are registered as a {role}.")
        return redirect('trips:index')

    return render(request, 'users/onboarding.html', {'user': request.user})


# ────────────────────────────────────────────────
# Dashboards
# ────────────────────────────────────────────────

@login_required
def driver_dashboard(request, username):
    profile_user = get_object_or_404(User, username=username)

    if profile_user.role != 'driver':
        messages.error(request, "This user is not a driver.")
        return redirect('trips:index')

    # Only the driver themselves or admins can view the full dashboard
    trips = Trip.objects.filter(created_by=profile_user).prefetch_related('passengers').select_related('start_node', 'end_node', 'current_node')

    return render(request, 'users/driver_dashboard.html', {
        'profile_user': profile_user,
        'trips': trips,
    })


@login_required
def passenger_dashboard(request):
    if request.user.role != 'passenger':
        messages.error(request, "Only passengers can access this dashboard.")
        return redirect('trips:index')

    booked_trips = request.user.booked_trips.exclude(status='cancelled').select_related('start_node', 'end_node', 'current_node')
    carpool_requests = CarpoolRequest.objects.filter(
        passenger=request.user
    ).prefetch_related('offers__driver', 'offers__trip').select_related('pickup_node', 'destination_node')

    return render(request, 'users/passenger_dashboard.html', {
        'profile_user': request.user,
        'trips': booked_trips,
        'requests': carpool_requests,
    })


@login_required
def dashboard_redirect(request, username=None):
    user = request.user
    if user.needs_onboarding:
        return redirect('users:onboarding')
    if user.role == 'driver':
        return redirect('users:driver_dashboard', username=user.username)
    if user.role == 'passenger':
        return redirect('users:passenger_dashboard')
    return redirect('trips:index')
