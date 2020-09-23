# Django Trips API

This is a Django Rest API for fetching and creating trips and schedules.
## Installation
Simply do:
```bash
pip install django-trips
```

## Usage
Add the app into your installed apps in your project's settings file. 
```
INSTALLED_APPS = [
    ...
    'django_trips',
]
```

Add the following to your root urls.py file.
```
urlpatterns = [
    ...
    url(r'^trips/', include('django_trips.urls'))
]
```
Note that the URL path can be whatever you want.

## Api
The following pages are served in the development:

| Page                 |  Method          | URL                                           |
|----------------------|------------------|-----------------------------------------------|
| Trips List           | GET              | http://localhost:8000/api/trips/              |
| Single Trip          | GET              | http://localhost:8000/api/trip/20/            |
| Update Trip          | PUT              | http://localhost:8000/api/trip/20/            |
| Delete Trip          | DELETE           | http://localhost:8000/api/trip/20/            |



## Develop Django Trips
Kick the docker build using the following command. 
```
make build
``` 
This task may take few minutes. 

 
Once the build has been completed, spin up the docker and migrate the database. 
```bash
> make run
> make shell 
> make update_db
```
Create a superuser with username `admin`.

``` bash
> make shell
> python manage.py createsuperuser
```

Create batch of trips. Run the following command inside docker shell.
```bash
> python manage.py  generate_trips --batch_size=100
OR
> make random_trips
```

## Docker Commands

| Action                            |  Command          |
|-----------------------------------|-------------------|
| Run Server                        | `make run`        |
| Trail Logs                        | `make logs`       |
| Attach sever                      | `make attach`     |
| Stop server                       | `make stop`       |
| * Destroy docker container.         | `make destory`    |

_* caution, this will remove all your data._

