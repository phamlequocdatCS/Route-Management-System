# Route-Management-System

Django, JavaScript + jQuery, OpenStreetMap, PostgreSQL

## Features checklist

- [x] Auth
  - [x] Super user
  - [x] Login
  - [x] Logout
  - [x] SU create user
    - [x] Create account
    - [x] Send confirmation email
  - [x] Reset password
    - [x] Request reset
    - [x] Send reset email
    - [x] New password
- [ ] Location
  - [x] Add location
  - [ ] Edit location
  - [ ] Delete location
  - [ ] Search locations
    - [ ] Filter by bookmark
- [x] Bookmarking
- [ ] Note
  - [x] Add note
  - [x] View notes
  - [ ] Delete notes
- [ ] Routing
  - [ ] Create a plan
  - [ ] View plan
  - [ ] Edit plan
  - [ ] Change plan status
  - [ ] Delete plan
- [x] Logging
  - [x] View logs
  - [x] Create logs
- [ ] x
- [ ] x

## Getting started

1. [Setup PostgreSQL](#setup-postgresql)
2. Git clone this repo
3. [Setup Python environment](#setup-python-environment)
4. [Setup Django](#setup-django-project)

### Setup PostgreSQL

Ensure **pgAdmin** is installed. Create a new server and database in pgAdmin:

Server

- Name: `routingSystem`
- Hostname: `localhost`
- Port: `5432`
- Username: `postgres`
- Password: `YOUR_PASSWORD` (change password in `Route-Management-System\theRouteManager\theRouteManager\secrets.py`)

Database Name: `routeManager`

### Setup Python environment

Tested with Python 3.10.12 on Windows

```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Setup Django project

```cmd
django-admin startproject theRouteManager   
cd theRouteManager
python manage.py startapp routeManager
```

## Quick commands

### Run migrations

```cmd
python manage.py makemigrations
python manage.py migrate
```

### Collect static files

```cmd
python manage.py collectstatic
```

### Run project

```cmd
python manage.py runserver
```

### Create superuser

```cmd
python manage.py createsuperuser
```
