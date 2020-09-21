# Django Trips API

This is a Django Rest API for fetching and creating trips and schedules.
## Installation
Simply do:
```bash
pip install django-trips
```

## Setup
* Kick the docker build using ``make build``. This can take sometime. 
* Migrate database. 
Once the build has been completed, spin up the docker and migrate the database. 
```bash
> make run
> make shell 
> make update_db
```
* Create a superuser with username `admin`.

``` bash
> make shell
> python manage.py createsuperuser
```
3. Create batch of trips `make new_trips`. This will create random (100) trips
```bash
> python manage.py new_trips
OR
> make new_trips
```

## Api
The following pages are served in the development:

| Page                 |  Method          | URL                            |
|----------------------|--------------|------------------------------------|
| Trips List           | GET |http://localhost:8000/trips/api/trips        |


## Docker Commands
#### Run server

`make run`

#### Server logs

`make logs`
#### Attach container
`make attach`

#### Stop Container
`make stop`

#### Destroy
_caution, this will remove all your data._ 

`make destory`
