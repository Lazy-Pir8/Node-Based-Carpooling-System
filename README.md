Node-Based Carpooling System

A web application for carpooling built with Django, Docker, PostgreSQL, and Nginx. Users can create trips, request rides, and manage driver offers. This project is deployed on an AWS EC2 VPS and can be accessed publicly.

🌐 Live Site

Check it out here: http://51.20.34.28/


Features - 
Drivers can create trips and set availability.
Passengers can request carpools and view available drivers.
Dynamic calculation of fares and detours.
Admin interface for managing users and trips (Django admin).
Fully containerized with Docker for easy deployment.

 Tech Stack - 
Backend: Django 5.2
Frontend: Django Templates + AI
Database: PostgreSQL
Server & Deployment: Docker, Gunicorn, Nginx, AWS EC2
Other: REST Framework for API endpoints

Setup & Installation  - 
Clone the repo:
git clone https://github.com/Lazy-Pir8/Node-Based-Carpooling-System.git
cd Node-Based-Carpooling-System
Create a .env file with your settings (example variables: DJANGO_SECRET_KEY, DATABASE_NAME, DATABASE_USER, etc.).
Build and run with Docker:
docker compose up --build -d
Apply migrations and create a superuser:
docker exec -it carpool_web python manage.py migrate
docker exec -it carpool_web python manage.py createsuperuser
Access the site locally: http://localhost:8000

 Admin Panel
Login at: http://YOUR_PUBLIC_IP/admin (Have not created a dedicated admin page, so only django-default administration for now)
Use the superuser credentials you created.

 Project Structure
Node-Based-Carpooling-System/
├─ carpool/              # Django project settings
├─ users/                # Custom user app
├─ trips/                # Carpooling trips & requests
├─ network/              # Nodes, points, and other location models
├─ Dockerfile
├─ docker-compose.yml
└─ .env                  # Environment variables (not pushed!)

 Deployment -
Hosted on AWS EC2 with Docker and Nginx.
Exposed via public IP (Directly IP for now, haven't given any domain name for now)
HTTPS is not enabled so HTTP for now

 Notes
Ensure .env is not committed — it contains sensitive keys.
Always run migrations after pulling new updates:
docker exec -it carpool_web python manage.py migrate
