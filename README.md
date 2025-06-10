# Django Trips API

This is a Django REST API for managing and retrieving trips, schedules, bookings, and related travel data.

This service is a core component of the [DestinationPak](https://destinationpak.com) project — a platform designed 
to make exploring and booking adventures across Pakistan easier and more accessible.

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
## Migrate
```
python manage.py migrate 
```
Add the following to your root `urls.py` or to your desired file location.   
```
urlpatterns = [
    ...
    path('trips/', include(('django_trips.api.urls', 'trips-api'), namespace='trips-api')),
]
```
You can replace `trips/` to any namespace you like for the api.

## Generate random trips.
Before you generate random scripts, make sure you have the required settings available in your project. If you want to use the default settings set `USE_DEFAULT_TRIPS=True`. 
The script depends upon these variables, if you don't want to use the default settings set the 
following settings. 
1. `TRIP_DESTINATIONS`
2. `TRIP_DEPARTURE_LOCATION`
3. `TRIP_LOCATIONS = TRIP_DEPARTURE_LOCATION + TRIP_DESTINATIONS`
4. `TRIP_HOSTS`
5. `TRIP_FACILITIES`
6. `TRIP_CATEGORIES`
7. `TRIP_GEARS`

```
python manage.py generate_trips --batch_size=100
``` 
Change the `batch_size` variable to create as much of trips you want. 

## Developer Docs & API Documentation
You can access the all available API endpoints on the following links.
* http://localhost:8000/api/v1/schema/redoc
* http://localhost:8000/api/v1/schema/swagger-ui/

## API Endpoints
The following pages are served in the development:

| Page                    | Method | URL                                                          |
|-------------------------|--------|--------------------------------------------------------------|
| All Trips List          | GET    | http://localhost:8000/api/v1/trips/                          |
| Upcoming Trips List     | GET    | http://localhost:8000/api/v1/trips/upcoming/                 |
| Search Trip             | GET    | http://localhost:8000/api/v1/trips/upcoming/?name=Boston/    |
| Single Trip             | GET    | http://localhost:8000/api/v1/trips/{identifier}/             |
| Update Trip             | PUT    | http://localhost:8000/api/v1/trips/{identifier}/             |
| Delete Trip             | DELETE | http://localhost:8000/api/v1/trips/{identifier}/             |
| Create Trip             | POST   | http://localhost:8000/api/v1/trips/                          |
| Destinations List       | GET    | http://localhost:8000/api/v1/destinations/                   |
| Destinations Detail     | GET    | _TODO_                                                         |
| All Trip Bookings       | GET    | http://localhost:8000/api/v1/trips/{trip_id}/bookings/       |
| Book a Trip             | POST   | http://localhost:8000/api/v1/trips/{trip_id}/bookings/create/ |
| Booking Details         | GET    | http://localhost:8000/api/v1/trips/bookings/{number}/        |
| Update Booking          | PUT    | http://localhost:8000/api/v1/trips/bookings/{number}/        |
| Cancel Booking          | POST   | http://localhost:8000/api/v1/trips/bookings/{number}/cancel/ |
| Review Trip             | GET    | _TODO_                                                         |
| Trip Reviews & Comments | GET    | _TODO_                                                         |




### API permissions
| Authentication          | Token Life |   
|-------------------------|------------|
| `SessionAuthentication` | UNLIMITED  |
| `JWTAuthentication`     | 7 Days     |


| Permissions       |
|-------------------|
| `IsAuthenticated` |
| `IsAdminUser`     |


## Develop Django Trips
Kick the docker build using the following command. 
```
make build
``` 
This task may take few minutes. 

 
Once the build has been completed, spin up the docker and migrate the database. 
```bash
> make dev.up
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

## Test
Run tests using the following command.
```
make tests
```
## Docker Commands

| Action                            | Command        |
|-----------------------------------|----------------|
| Run Server                        | `make dev.up`  |
| Trail Logs                        | `make logs`    |
| Attach sever                      | `make attach`  |
| Stop server                       | `make stop`    |
| * Destroy docker container.       | `make destory` |

_* caution, this will remove all your data._

## How to Contribute

Contributions are welcome! Whether it's bug fixes, new features, 
improving documentation, or sharing feedback — we'd love your help.

Please fork the repository, make your changes in a feature branch, 
and submit a pull request. For major changes, consider opening an issue
first to discuss what you’d like to work on.

---

Thank you for being a part of the Django Trips journey.  
Together, we can make travel management smarter, faster, and more delightful.

Reach out in you need further assistance.
`admin@destinationpak.com`

Happy coding! ✨