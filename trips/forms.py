from django import forms
from .models import Trip


class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = ['name', 'departure_time', 'arrival_time', 'start_node', 'end_node', 'ticket_price', 'available_seats']
        widgets = {
            'departure_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'arrival_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('start_node')
        end = cleaned.get('end_node')
        depart = cleaned.get('departure_time')
        arrive = cleaned.get('arrival_time')

        if start and end and start == end:
            raise forms.ValidationError("Start and end nodes must be different.")

        if depart and arrive and arrive <= depart:
            raise forms.ValidationError("Arrival time must be after departure time.")

        return cleaned
