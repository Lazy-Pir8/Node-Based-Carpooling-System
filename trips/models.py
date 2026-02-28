from django.db import models

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
    def __str__(self):
        return f"{self.driver} - {self.start_node} to {self.end_node} at {self.departure_time}"
