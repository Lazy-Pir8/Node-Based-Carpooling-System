from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
User = get_user_model()
# Create your models here.

class Trip(models.Model):
    name = models.CharField(max_length=100)
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
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,related_name="created_trips", on_delete=models.CASCADE, null=True, blank=True)
    def __str__(self):
        return f"{self.name} - {self.start_node} to {self.end_node} at {self.departure_time}"

