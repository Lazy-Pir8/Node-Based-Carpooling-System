
```markdown
# Node-Based Carpooling System

A web application for carpooling built with Django, Docker, PostgreSQL, and Nginx. Users can create trips, request rides, and manage driver offers. This project is deployed on an AWS EC2 VPS and can be accessed publicly.

## Live Site

Check it out here: [http://51.20.34.28/](http://51.20.34.28/)

## Features

* **Drivers:** Can create trips and set availability.
* **Passengers:** Can request carpools and view available drivers.
* **Logic:** Dynamic calculation of fares and detours.
* **Management:** Admin interface for managing users and trips (Django admin).
* **Infrastructure:** Fully containerized with Docker for easy deployment.

## Tech Stack

* **Backend:** Django 5.2
* **Frontend:** Django Templates + AI
* **Database:** PostgreSQL
* **Server & Deployment:** Docker, Gunicorn, Nginx, AWS EC2
* **Other:** REST Framework for API endpoints

## Setup & Installation

1.  **Clone the repo:**
    ```bash
    git clone [https://github.com/Lazy-Pir8/Node-Based-Carpooling-System.git](https://github.com/Lazy-Pir8/Node-Based-Carpooling-System.git)
    cd Node-Based-Carpooling-System
    ```

2.  **Environment Setup:**
    Create a `.env` file in the root directory with your settings (example variables: `DJANGO_SECRET_KEY`, `DATABASE_NAME`, `DATABASE_USER`, etc.).

3.  **Build and run with Docker:**
    ```bash
    docker compose up --build -d
    ```

4.  **Apply migrations and create a superuser:**
    ```bash
    docker exec -it carpool_web python manage.py migrate
    docker exec -it carpool_web python manage.py createsuperuser
    ```

5.  **Access the site locally:**
    [http://localhost:8000](http://localhost:8000)

## Admin Panel

* **URL:** `http://whateverIp/admin`
* **Note:** A dedicated admin page hasn't been created yet, so the project uses the default Django administration for now.
* **Access:** Use the superuser credentials created during the setup steps.
username - admin
pass - admin@123

## Project Structure

```text
Node-Based-Carpooling-System/
├─ carpool/              # Django project settings
├─ users/                # Custom user app
├─ trips/                # Carpooling trips & requests
├─ network/              # Nodes, points, and other location models
├─ Dockerfile
├─ docker-compose.yml
└─ .env                  # Environment variables (not pushed!)
```

## Deployment

* Hosted on **AWS EC2** using Docker and Nginx.
* Exposed via public IP (Direct IP access; no domain name assigned yet).
* **Protocol:** HTTP (HTTPS is not yet enabled).

## Notes

* **Security:** Ensure `.env` is included in your `.gitignore` and never committed to the repository as it contains sensitive keys.
* **Maintenance:** Always run migrations after pulling new updates:
    ```bash
    docker exec -it carpool_web python manage.py migrate
    ```
```

---
