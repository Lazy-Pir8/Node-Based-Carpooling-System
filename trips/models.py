from django.db import models

# Create your models here.

class Trip(models.Model):
    driver = models.CharField(max_length=100)
    start_node = models.ForeignKey(
        'network.Node', related_name='start_node', on_delete=models.CASCADE
    )
    end_node = models.ForeignKey(
        'network.Node', related_name='end_node', on_delete=models.CASCADE
    )
    
    max_passengers = models.IntegerField()
    departure_time = models.DateTimeField()
    available_seats = models.IntegerField()
