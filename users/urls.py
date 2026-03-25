from django.urls import path
from . import views
from django.contrib.auth.views import LoginView, LogoutView

app_name = 'users'

urlpatterns = [
    
    path('login/', LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', views.register_view, name='register'),    
    # path('profile/<str:username>/', views.profile_view, name='profile'),
    path('dashboard/<str:username>/', views.dashboard_redirect, name='dashboard'),
    path('driver_dashboard/<str:username>/', views.driver_dashboard, name='driver_dashboard'),
    path('passenger_dashboard/', views.passenger_dashboard, name='passenger_dashboard'),

]