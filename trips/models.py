from django.db import models

# Create your models here.

class Trip(models.Model):
    driver = models.CharField(max_length=100)
    start_node = models.CharField(max_length=100)
    end_node = models.CharField(max_length=100)
    current_node = models.CharField(max_length=100)
    max_passengers = models.IntegerField()
    departure_time = models.DateTimeField()
    available_seats = models.IntegerField()
