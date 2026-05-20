from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_CHOICES = (
        ('passenger', 'Passenger'),
        ('driver', 'Driver'),
        ('admin', 'Admin'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, null=True, blank=True, default='driver')
    phone_number = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.username

    @property
    def is_driver(self):
        return self.role == 'driver'

    @property
    def is_passenger(self):
        return self.role == 'passenger'

    @property
    def needs_onboarding(self):
        return self.role is None
