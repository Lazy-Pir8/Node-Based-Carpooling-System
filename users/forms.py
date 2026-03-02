from django import forms
from django.forms import ModelForm
from django.contrib.auth import get_user_model
User = get_user_model()

class PassengerForm(ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number']

class DriverForm(ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number']



class RegisterForm(ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role']  