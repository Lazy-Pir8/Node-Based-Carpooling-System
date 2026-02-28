from django import forms
from django.forms import ModelForm
from .models import User

class PassengerForm(ModelForm):
    class Meta:
        model = Passenger
        fields = ['name', 'email', 'phone_number']

class DriverForm(ModelForm):
    class Meta:
        model = Driver
        fields = ['name', 'email', 'phone_number']

class LoginForm(forms.Form):
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput)

class RegisterForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    phone_number = forms.CharField(max_length=20, required=False)
    password = forms.CharField(widget=forms.PasswordInput)
    role = forms.ChoiceField(choices=[('passenger', 'Passenger'), ('driver', 'Driver')])
