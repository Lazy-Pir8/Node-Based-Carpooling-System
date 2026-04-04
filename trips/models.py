from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
User = get_user_model()
from network.models import Node, Edge
from django.utils.text import slugify
from django.utils.timezone import now
# Create your models here.

class Trip(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    start_node = models.ForeignKey(
        'network.Node', related_name='start_node', on_delete=models.CASCADE
    )
    end_node = models.ForeignKey(
        'network.Node', related_name='end_node', on_delete=models.CASCADE
    )
    
    id = models.AutoField(primary_key=True)
    departure_time = models.DateTimeField()
    available_seats = models.IntegerField()
    arrival_time = models.DateTimeField(null=True, blank=True)
    ticket_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,related_name="created_trips", on_delete=models.CASCADE, null=False, blank=False)
    passengers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='booked_trips', blank=True)
    current_node = models.ForeignKey(Node, null=True, on_delete=models.SET_NULL)
    started = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)



    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            self.slug = f"{base_slug}-{int(now().timestamp())}"
        super().save(*args, **kwargs)
    def __str__(self):
        return f"{self.name} - {self.start_node} to {self.end_node} at {self.departure_time}"




class TripNode(models.Model):
    trip = models.ForeignKey('Trip',related_name='trip_nodes', on_delete=models.CASCADE)
    node = models.ForeignKey(Node, on_delete=models.CASCADE)
    order = models.IntegerField()
    is_passed = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.trip.id} - {self.node.point} (Order: {self.order})"


class CarpoolRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('matched', 'Matched'),
        ('cancelled', 'Cancelled'),
    )

    passenger = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    pickup_node = models.ForeignKey('network.Node', related_name='pickup_requests', on_delete=models.CASCADE)
    destination_node = models.ForeignKey('network.Node', related_name='destination_requests', on_delete=models.CASCADE)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

class DriverOffer(models.Model):
    request = models.ForeignKey(CarpoolRequest, related_name='offers', on_delete=models.CASCADE)
    driver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    trip = models.ForeignKey('trips.Trip', on_delete=models.CASCADE)

                
    detour_distance = models.FloatField(default=0)   
    fare = models.DecimalField(max_digits=10, decimal_places=2)

    is_selected = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    detour = models.IntegerField(default=0)  
"""
class CarpoolServiceStatus(models.Model):
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return "Active" if self.is_active else "Suspended"
"""