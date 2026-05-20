from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('trips/', include('trips.urls')),
    path('', include('trips.urls')),           # index at /
    path('accounts/', include('allauth.urls')), # Google OAuth
]
