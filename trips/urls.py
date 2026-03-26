from django.urls import path
from . import views

app_name = 'trips'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('book_trip/<str:slug>/', views.BookTripView.as_view(), name='book_trip'),
    path('trip_detail/<str:slug>/', views.TripDetailView.as_view(), name='trip_detail'),
    path('trips/', views.ListTripsView.as_view(), name='list_trips'),
    path('create/', views.create_trip, name='create_trip'),
    path('create_request/', views.create_request, name='create_request'),
    path('request_offers/<int:request_id>/', views.request_offers, name='request_offers'),
    path('offer_accept/<int:offer_id>/', views.accept_offer, name='offer_accept'),
    path('cancel_offer/<int:request_id>/', views.cancel_offer, name='cancel_offer'),
    path('driver_requests/<int:trip_id>/', views.driver_offers, name='driver_requests'),
    path('create_offer/<int:request_id>/<int:trip_id>/', views.create_offer, name='create_offer'),
]