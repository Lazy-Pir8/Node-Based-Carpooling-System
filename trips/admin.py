from django.contrib import admin
from .models import Trip, TripNode, CarpoolRequest, DriverOffer, CarpoolServiceStatus


class TripNodeInline(admin.TabularInline):
    model = TripNode
    extra = 0
    readonly_fields = ('order', 'is_passed')


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_node', 'end_node', 'status', 'departure_time', 'available_seats', 'created_by')
    list_filter = ('status',)
    search_fields = ('name', 'created_by__username')
    inlines = [TripNodeInline]


@admin.register(CarpoolRequest)
class CarpoolRequestAdmin(admin.ModelAdmin):
    list_display = ('passenger', 'pickup_node', 'destination_node', 'status', 'created_at')
    list_filter = ('status',)


@admin.register(DriverOffer)
class DriverOfferAdmin(admin.ModelAdmin):
    list_display = ('driver', 'request', 'trip', 'detour', 'fare', 'is_selected')


@admin.register(CarpoolServiceStatus)
class CarpoolServiceStatusAdmin(admin.ModelAdmin):
    list_display = ('is_active',)

    def has_add_permission(self, request):
        # Only allow one instance
        return not CarpoolServiceStatus.objects.exists()
