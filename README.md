# Route Management System

Django, JavaScript + jQuery, OpenStreetMap + Open Source Routing Machine, PostgreSQL

See [demo.md](demo.md) for demonstration of the project

## Getting started

<!-- no toc -->
1. [Setup PostgreSQL](#setup-postgresql)
2. Git clone this repo
3. [Setup Python environment](#setup-python-environment)
4. [Setup Django](#setup-django-project)
5. [Setup Email service](#setup-email-service)
6. [Setup OSRM service](#setup-osrm-service)

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

### Setup Email service

Set the `gmail_app_password, gmail_app_email` in `secrets.py`

### Setup OSRM service

1. Download the Windows Release binary at <https://github.com/Project-OSRM/osrm-backend/wiki/Windows-Compilation>
2. Extract the content to `Route-Management-System\osrm_Release`
3. Download the region-of-interest OpenStreetMap data (Ex. <https://download.geofabrik.de/asia/vietnam.html> `osrm_Release\vietnam-latest.osm.pbf`)
4. Pre-process the data (it will take a while)

    ```cmd
    osrm-extract.exe -p car.lua "vietnam-latest.osm.pbf"
    osrm-contract "vietnam-latest.osrm"
    ```

5. Run the server:

    ```cmd
    osrm-routed.exe vietnam-latest.osrm
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
cd Route-Management-System\theRouteManager
python manage.py runserver
```

### Create superuser

```cmd
python manage.py createsuperuser
```
