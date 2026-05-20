from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views

app_name = 'users'

urlpatterns = [
    path('login/', LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='trips:index'), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('onboarding/', views.onboarding, name='onboarding'),
    path('dashboard/', views.dashboard_redirect, name='dashboard'),
    path('driver/<str:username>/', views.driver_dashboard, name='driver_dashboard'),
    path('passenger/', views.passenger_dashboard, name='passenger_dashboard'),
]
