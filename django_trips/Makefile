.DEFAULT_GOAL := test
NODE_BIN=$(CURDIR)/node_modules/.bin

.PHONY:static run shell

requirements: ## install development environment requirements
	pip install -qr requirements.txt --exists-action w

update_db: ## Install migrations
	python manage.py migrate

new_trips: ## Adds random trips
	python manage.py  generate_trips --batch_size=100

static: ## Gather all static assets for production
	python manage.py collectstatic -v 0 --noinput

help: ## display this help message
	@echo "Please use \`make <target>' where <target> is one of"
	@grep '^[a-zA-Z]' $(MAKEFILE_LIST) | sort | awk -F ':.*?## ' 'NF==2 {printf "\033[36m  %-25s\033[0m %s\n", $$1, $$2}'

test: ## Run unit tests for Trips app
	python manage.py test trips/tests

build: destroy _build

_build: 
	find . -type p -delete
	docker-compose build

stop:  ## Stop all services
	docker-compose stop
run: # Run the server
	docker-compose up -d --remove-orphans

restart: # Restart the server
	docker restart djangotrips.django

attach: ## Attach to the django container process to use the debugger & see logs.
	docker attach djangotrips.django

logs: # Attach logs for the django server
	docker-compose -f docker-compose.yml logs -f --tail=100 trips

shell: ## Enter in django shell
	docker exec -it djangotrips.django /bin/bash

destroy: stop ## Remove all devstack-related containers, networks, and volumes
	docker-compose -f ./docker-compose.yml down -v

