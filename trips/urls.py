from django.urls import path
from . import views

app_name = 'trips'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('list/', views.ListTripsView.as_view(), name='list_trips'),
    path('detail/<str:slug>/', views.TripDetailView.as_view(), name='trip_detail'),
    path('create/', views.create_trip, name='create_trip'),
    path('cancel/<int:trip_id>/', views.cancel_trip, name='cancel_trip'),

    # Carpool requests – passenger
    path('request/create/', views.create_request, name='create_request'),
    path('request/<int:request_id>/offers/', views.request_offers, name='request_offers'),
    path('request/<int:request_id>/cancel/', views.cancel_request, name='cancel_request'),
    path('offer/<int:offer_id>/accept/', views.accept_offer, name='offer_accept'),

    # Carpool requests – driver
    path('driver/requests/<int:trip_id>/', views.driver_requests_view, name='driver_requests'),
    path('driver/offer/create/<int:request_id>/<int:trip_id>/', views.create_offer, name='create_offer'),
    path('driver/offer/<int:offer_id>/accept/', views.driver_accept_offer, name='driver_accept_offer'),

    # DRF API endpoints
    path('api/trip/<int:trip_id>/update_node/', views.update_current_node, name='api_update_node'),
    path('api/trip/<int:trip_id>/status/', views.get_trip_status, name='api_trip_status'),
    path('api/trip/<int:trip_id>/requests/', views.list_carpool_requests_api, name='api_trip_requests'),
]
