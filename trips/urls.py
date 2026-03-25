from django.urls import path
from . import views

app_name = 'trips'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('book_trip/<str:slug>/', views.BookTripView.as_view(), name='book_trip'),
    path('trip_detail/<str:slug>/', views.TripDetailView.as_view(), name='trip_detail'),
    path('trips/', views.ListTripsView.as_view(), name='list_trips'),
    path('create/', views.create_trip, name='create_trip'),
]