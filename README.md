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

## API Endpoints
The following pages are served in the development:

| Page                 |  Method          | URL                                                        |
|----------------------|------------------|-----------------------------------------------             |
| Scheduled Trips List | GET              | http://localhost:8000/api/trips/                           |
| Available Trips List | GET              | http://localhost:8000/api/trips/by/availability/           |
| Search Trip          | GET              | http://localhost:8000/api/trips?name=Boston/            |
| Single Trip          | GET              | http://localhost:8000/api/trip/trip-id-or-slug/            |
| Update Trip          | PUT              | http://localhost:8000/api/trip/trip-id-or-slug/            |
| Update Trip          | PATCH            | http://localhost:8000/api/trip/trip-id-or-slug/            |
| Delete Trip          | DELETE           | http://localhost:8000/api/trip/trip-id-or-slug/            |
| Destination          | GET              | http://localhost:8000/api/destinations/                    |
| Destination Detail   | GET              | http://localhost:8000/api/destination/location-slug        |
| All Trip Bookings    | GET              | http://localhost:8000/api/trip/bookings                    |
| Single Bookings      | GET              | http://localhost:8000/api/trip/booking/id                  |
| Single Trip Bookings | GET              | http://localhost:8000/api/trip/<trip-slug>/bookings        |       |


### API permissions
| Authentication            
|-------------------------- |
| `SessionAuthentication`   |
| `BasicAuthentication`     |

| Permissions               |
|-------------------------  |
|   `IsAuthenticated`       | 


### Trip List
`http://localhost:8000/api/trips/`

This endpoint is used to list all the trips by schedule using the **GET** request type. These trips have specified 
(fixed) schedule. These trips use django model `TripSchedule` for creating their schedule. Once the schedule is expired,
these trips do not renew automatically. 
These are the trip with "**static**" schedule data.

### Trip List by Availability
`http://localhost:8000/api/trips/by/availability/`

There is another mechanism which would like you to define dynamic trips schedule. Which is using `TripAvailability` 
model. In this model you can define the recurrence of any trip, weekly, daily, or monthly and these trip may
auto-renew themselves. They come handy when you have dynamic trips schedule.    

### Search Trip
`http://localhost:8000/api/trip/id-or-slug?destination=<destination name, destination name 2,>`

Search specific trips. Here are the params that can be passed while searching. You can also mix the params together to
narrow down the search. 

| param                 | description                                                           | example                           |
| ---                   | ---                                                                   |---                                |
| name (str)               | Find trips that contains specific name.                               | `/api/trips/?name=Boston`
| destination[]         | Filter trips with specific destinations.                              | `destination=Boston,London`
| price_from (str)      | Find trips that has price greater than or equal to the given amount   | `/api/trips/?price_from=200`
| price_to (str)        | Find trips that has price less than or equal to the given amount      | `/api/trips/?price_to=200`
| duration_from (int)   | Find trips having duration greater than or equal to the given number  | `/api/trips/?duration_from=2`
| duration_to (int)     | Find trips having duration less  than or equal to the given number    | `/api/trips/?duration_to=10`
| date_from (date)      | Find trips that are scheduled greater than or specified date `<yyyy-mm-dd>`          | `/api/trips/?date_from=2020-01-02`
| date_to (date)        | Find trips that are scheduled less than or equal to specified date`<yyyy-mm-dd>`    | `/api/trips/?date_from=2020-01-02`



### Single Trip
`http://localhost:8000/api/trip/id-or-slug`

This endpoint is used to fetch a single trip using GET request type.

### Update Trip (using PUT)
`http://localhost:8000/api/trip/trip-id-or-slug/`

This endpoint is used to update a single trip using PUT request type. You would need to pass the complete trip object. 
```python
reset_of_params = {}
data = {
    'age_limit': 39,
    **reset_of_params,
}
```
### Update Trip (using PATCH)
`http://localhost:8000/api/trip/trip-id-or-slug/`
```python
data = {
    'age_limit': 39,
}
```
### Update Trip (using PUT)
`http://localhost:8000/api/trip/trip-id-or-slug/`

This endpoint is used to delete a single trip using DELETE request type. 

### Get Destinations List
`http://localhost:8000/api/destinations/`

This endpoint is used to fetch all destinations available.  

### Get Destination Detail
`http://localhost:8000/api/destination/destination-slug`

Given a slug, this endpoint provides detail about a single trip.

### Create Trip booking
`http://localhost:8000/api/trip/bookings`

#### GET:
Get all the trips list using the `GET` request method. 
#### POST:
Create trip booking by giving the following "example" data in the `POST` request.
```
{
    "name": "tom latham",
    "trip": "5-days-trip-to-city-center",
    "phone_number": "tom",
    "cnic_number": "1234234-23423",
    "email": "a@gmail.com",
    "target_date": "2021-09-01",
    "message": "Tom booking# 1"
}
```

### Single Trip booking Operations 
`http://localhost:8000/api/trip/booking/<booking-id>/`

Retrieve, Update & Delete a single trip booking. 

### All Trip Bookings
`http://localhost:8000/api/trip/<trip-slug>bookings/`

Retrieve all bookings of a single trip.

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

## Test
Run tests using the following command.
```
make tests
```
## Docker Commands

| Action                            |  Command          |
|-----------------------------------|-------------------|
| Run Server                        | `make run`        |
| Trail Logs                        | `make logs`       |
| Attach sever                      | `make attach`     |
| Stop server                       | `make stop`       |
| * Destroy docker container.       | `make destory`    |

_* caution, this will remove all your data._

## How to Contribute
Contributions are welcome!