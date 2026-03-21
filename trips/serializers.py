from rest_framework import serializers
from .models import Trip, TripNode

class TripNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TripNode
        fields = ['node', 'order']

class TripSerializer(serializers.ModelSerializer):

    class Meta:
        model = Trip
        fields = '__all__'

