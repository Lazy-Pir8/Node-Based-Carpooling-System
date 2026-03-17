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
    
  
    departure_time = models.DateTimeField()
    available_seats = models.IntegerField()
    arrival_time = models.DateTimeField(null=True, blank=True)
    ticket_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,related_name="created_trips", on_delete=models.CASCADE, null=False, blank=False)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            self.slug = f"{base_slug}-{int(now().timestamp())}"
        super().save(*args, **kwargs)
    def __str__(self):
        return f"{self.name} - {self.start_node} to {self.end_node} at {self.departure_time}"



class TripNode(models.Model):
    trip = models.ForeignKey('Trip', on_delete=models.CASCADE)
    node = models.ForeignKey(Node, on_delete=models.CASCADE)
    order = models.IntegerField()

    def __str__(self):
        return f"{self.trip.id} - {self.node.point} (Order: {self.order})"