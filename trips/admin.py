from django.contrib import admin
from .models import Trip
# Register your models here.

@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('driver', 'start_node', 'end_node', 'max_passengers', 'departure_time', 'available_seats',
    'max_passengers', 'departure_time', 'available_seats',)
    search_fields = ('driver', 'start_node__point', 'end_node__point', )
