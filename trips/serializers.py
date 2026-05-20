from rest_framework import serializers
from .models import Trip, TripNode, CarpoolRequest, DriverOffer


class TripNodeSerializer(serializers.ModelSerializer):
    node_name = serializers.CharField(source='node.name', read_only=True)

    class Meta:
        model = TripNode
        fields = ['order', 'node', 'node_name', 'is_passed']


class TripSerializer(serializers.ModelSerializer):
    trip_nodes = TripNodeSerializer(many=True, read_only=True)
    current_node_name = serializers.CharField(source='current_node.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = Trip
        fields = [
            'id', 'name', 'slug', 'start_node', 'end_node',
            'departure_time', 'arrival_time', 'available_seats',
            'ticket_price', 'status', 'created_by', 'created_by_username',
            'current_node', 'current_node_name', 'trip_nodes',
        ]
        read_only_fields = ['created_by', 'slug']


class CarpoolRequestSerializer(serializers.ModelSerializer):
    passenger_username = serializers.CharField(source='passenger.username', read_only=True)
    pickup_node_name = serializers.CharField(source='pickup_node.name', read_only=True)
    destination_node_name = serializers.CharField(source='destination_node.name', read_only=True)

    class Meta:
        model = CarpoolRequest
        fields = [
            'id', 'passenger', 'passenger_username',
            'pickup_node', 'pickup_node_name',
            'destination_node', 'destination_node_name',
            'status', 'created_at',
        ]
        read_only_fields = ['passenger', 'status']


class DriverOfferSerializer(serializers.ModelSerializer):
    driver_username = serializers.CharField(source='driver.username', read_only=True)

    class Meta:
        model = DriverOffer
        fields = [
            'id', 'request', 'driver', 'driver_username',
            'trip', 'detour', 'fare', 'is_selected', 'created_at',
        ]
        read_only_fields = ['driver', 'detour', 'fare', 'is_selected']
