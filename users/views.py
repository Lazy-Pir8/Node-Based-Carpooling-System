from django.shortcuts import render

# Create your views here.

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)

    return render(request, 'users/login.html')

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        form.save()
        if form.role == 'passenger':
            Passenger.objects.create(
                name=form.name,
                email=form.email,
                phone_number=form.phone_number
            )
            if form.is_valid():
                form.save()
                return render(request, 'trips/index.html')

        if form.role == 'driver':
            Driver.objects.create(
                name=form.name,
                email=form.email,
                phone_number=form.phone_number
            )
            if form.is_valid():
                form.save()
                return render(request, 'trips/index.html')
    

    return render(request, 'users/register.html')