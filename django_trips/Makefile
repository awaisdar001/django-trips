.DEFAULT_GOAL := test
NODE_BIN=$(CURDIR)/node_modules/.bin

.PHONY:static,run

requirements: ## install development environment requirements
	pip install -qr requirements.txt --exists-action w

update_db: ## Install migrations
	python manage.py migrate

new_trips: ## Adds random trips
	python manage.py  generate_trips --batch_size=100

static: ## Gather all static assets for production
	npm install
	python manage.py collectstatic -v 0 --noinput

help: ## display this help message
	@echo "Please use \`make <target>' where <target> is one of"
	@grep '^[a-zA-Z]' $(MAKEFILE_LIST) | sort | awk -F ':.*?## ' 'NF==2 {printf "\033[36m  %-25s\033[0m %s\n", $$1, $$2}'

test: ## Run unit tests for Trips app
	python manage.py test djangoapps/trips/tests

import: ## Import the mysql data into database
	mysql -uroot -p -h localhost djreact < ../data/djreact_2019-04-17.sql

build: _build
	find . -type p -delete
	docker-compose build
_build: 
	find . -type p -delete
	docker-compose build

stop:  ## Stop all services
	docker-compose stop
run:
	docker-compose up -d --remove-orphans

%-restart:
	docker restart trips.$*

%-attach: ## Attach to the specified service container process to use the debugger & see logs.
	## make app-attach
	docker attach trips.$*

logs:
	docker-compose -f docker-compose.yml logs -f --tail=100 trips

%-shell: ## Run a shell on the specified service container
	## make mysql-shell
	## make app-shell
	docker exec -it trips.$* /bin/bash

destroy: stop ## Remove all devstack-related containers, networks, and volumes
	docker-compose -f ./docker-compose.yml down
	bash ./scripts/destroy.sh

update_passwd:
	docker exec -u 0 -it trips.app bash