from rest_framework import serializers
from .models import Trip, TripNode

class TripNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TripNode
        fields = ['node', 'order']

class TripSerializer(serializers.ModelSerializer):
    trip_nodes = TripNodeSerializer(many=True, read_only=True, source='tripnode_set')

    class Meta:
        model = Trip
        fields = [
            'id',
            'start_node',
            'end_node',
            'created_by',
            'trip_nodes'
        ]
        read_only_fields = ['created_by']

