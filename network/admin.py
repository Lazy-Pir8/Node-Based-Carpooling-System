from django.contrib import admin
from .models import Node, Edge
# Register your models here.

@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Edge)
class EdgeAdmin(admin.ModelAdmin):
    list_display = ('from_node', 'to_node')
    search_fields = ('from_node__name', 'to_node__name')