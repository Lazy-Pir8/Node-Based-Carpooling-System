from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils.timezone import now


class Trip(models.Model):
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    start_node = models.ForeignKey(
        'network.Node', related_name='trips_starting_here', on_delete=models.CASCADE
    )
    end_node = models.ForeignKey(
        'network.Node', related_name='trips_ending_here', on_delete=models.CASCADE
    )
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField(null=True, blank=True)
    available_seats = models.PositiveIntegerField(default=4)
    ticket_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="created_trips",
        on_delete=models.CASCADE
    )
    passengers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='booked_trips',
        blank=True
    )
    current_node = models.ForeignKey(
        'network.Node',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='trips_currently_here'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            self.slug = f"{base_slug}-{int(now().timestamp())}"
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        return self.status == 'active'

    @property
    def is_completed(self):
        return self.status == 'completed'

    def __str__(self):
        return f"{self.name} ({self.start_node} → {self.end_node})"


class TripNode(models.Model):
    trip = models.ForeignKey('Trip', related_name='trip_nodes', on_delete=models.CASCADE)
    node = models.ForeignKey('network.Node', on_delete=models.CASCADE)
    order = models.IntegerField()
    is_passed = models.BooleanField(default=False)

    class Meta:
        ordering = ['order']
        unique_together = ('trip', 'order')

    def __str__(self):
        return f"{self.trip.id} - {self.node.name} (Order: {self.order})"


class CarpoolRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('cancelled', 'Cancelled'),
    )

    passenger = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='carpool_requests')
    pickup_node = models.ForeignKey('network.Node', related_name='pickup_requests', on_delete=models.CASCADE)
    destination_node = models.ForeignKey('network.Node', related_name='destination_requests', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.passenger.username}: {self.pickup_node} → {self.destination_node} [{self.status}]"


class DriverOffer(models.Model):
    request = models.ForeignKey(CarpoolRequest, related_name='offers', on_delete=models.CASCADE)
    driver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='driver_offers')
    trip = models.ForeignKey('Trip', on_delete=models.CASCADE, related_name='offers')
    detour = models.IntegerField(default=0)          # extra nodes vs original route
    fare = models.DecimalField(max_digits=10, decimal_places=2)
    is_selected = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Offer by {self.driver.username} for request {self.request.id}"


class CarpoolServiceStatus(models.Model):
    """Singleton model. Use CarpoolServiceStatus.get_solo() to access."""
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Carpool Service Status"
        verbose_name_plural = "Carpool Service Status"

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Active" if self.is_active else "Suspended"
