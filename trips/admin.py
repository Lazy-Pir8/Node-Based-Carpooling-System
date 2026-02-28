from django.contrib import admin
from .models import Trip
# Register your models here.

@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_node', 'end_node', 'ticket_price', 'departure_time', 'available_seats',)
    search_fields = ('name', 'start_node__point', 'end_node__point', )
