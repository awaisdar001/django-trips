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
Add the following to your root urls.py file. 
```
urlpatterns = [
    ...
    url(r'^trips/', include('django_trips.urls'))
]
```
You can replace `trips/` to any namespace you like for the api.

## Generate random trips.

```
python manage.py generate_trips --batch_size=100
``` 
Change the `batch_size` variable to create as much of trips you want. 

## API Endpoints
The following pages are served in the development:

| Page                 |  Method          | URL                                                        |
|----------------------|------------------|-----------------------------------------------             |
| Trips List           | GET              | http://localhost:8000/api/trips/                           |
| Search Trip          | GET              | http://localhost:8000/api/trips?name=Islamabad/            |
| Single Trip          | GET              | http://localhost:8000/api/trip/trip-id-or-slug/            |
| Update Trip          | PUT              | http://localhost:8000/api/trip/trip-id-or-slug/            |
| Update Trip          | PATCH            | http://localhost:8000/api/trip/trip-id-or-slug/            |
| Delete Trip          | DELETE           | http://localhost:8000/api/trip/trip-id-or-slug/            |

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

This endpoint is used to list all the trips Using the GET request type.

### Search Trip
`http://localhost:8000/api/trip/id-or-slug`

Search specific trips. Here are the params that can be passed while searching. You can also mix the params together to
narrow down the search. 

| param                 | description                                                           | example                           |
| ---                   | ---                                                                   |---                                |
| name ""               | Find trips that contains specific name.                               | `/api/trips/?name=Islamabad`
| destination[]         | Filter trips with specific destinations.                              | `destination=lahore,islamabad`
| price_from (str)      | Find trips that has price greater than or equal to the given amount   | `/api/trips/?price_from=200`
| price_to (str)        | Find trips that has price less than or equal to the given amount      | `/api/trips/?price_to=200`
| duration_from (int)   | Find trips having duration greater than or equal to the given number  | `/api/trips/?duration_from=2`
| duration_to (int)     | Find trips having duration less  than or equal to the given number    | `/api/trips/?duration_to=10`
| date_from (date)      | Find trips that are scheduled greater than or specified date          | `/api/trips/?date_from=2020-01-02`
| date_to (date)        | Find trips that are scheduled less than or equal to specified date    | `/api/trips/?date_from=2020-01-02`



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