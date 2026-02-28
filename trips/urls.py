from django.urls import path
from . import views

app_name = 'trips'

urlpatterns = [
    path('', views.index, name='index'),
    path('add_trip/', views.add_trip, name='add_trip'),
    path('book_trip/', views.book_trip, name='book_trip'),
]