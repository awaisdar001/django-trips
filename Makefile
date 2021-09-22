.DEFAULT_GOAL := test
NODE_BIN=$(CURDIR)/node_modules/.bin
MANAGE_PY_PATH = python manage.py

.PHONY: requirements update_db random_trips static help test build pull \
		_build stop run restart attach shell destroy

requirements: ## install development environment requirements
	pip install -qr requirements.txt --exists-action w

update_db: ## Install migrations
	$(MANAGE_PY_PATH) migrate

random_trips: ## Adds random trips
	$(MANAGE_PY_PATH)  generate_trips --batch_size=100

static: ## Gather all static assets for production
	$(MANAGE_PY_PATH) collectstatic -v 0 --noinput

help: ## display this help message
	@echo "Please use \`make <target>' where <target> is one of"
	@grep '^[a-zA-Z]' $(MAKEFILE_LIST) | sort | awk -F ':.*?## ' 'NF==2 {printf "\033[36m  %-25s\033[0m %s\n", $$1, $$2}'

test: ## Run unit tests for Trips app
	pytest -v

build: destroy _build

pull:
	docker-compose pull

_build: 
	find . -type p -delete
	docker-compose build

stop:  ## Stop all services
	docker-compose stop

run: # Run the server
	docker-compose up -d --remove-orphans

restart: # Restart the server
	docker restart djangotrips.django
	docker restart djangotrips.mysql

attach: ## Attach to the django container process to use the debugger & see logs.
	docker attach djangotrips.django

logs: trips-logs ## Run a shell on django container
trips-logs: ## Run a shell on the django service container
	docker-compose -f docker-compose.yml logs -f --tail=100 trips

mysql-logs: ## Run a shell on the mysql service container
	docker-compose -f docker-compose.yml logs -f --tail=100 tripsdb


shell: django-shell ## Run a shell on django container
django-shell: ## Run django shell
	docker exec -it djangotrips.django /bin/bash

mysql-shell: ## Run mysql shell
	docker exec -it djangotrips.mysql /bin/bash

destroy: stop ## Remove all containers, networks, and volumes
	docker-compose down -v

_move:
	mkdir -p src
	rm -rf src/django_trips
	cp {setup.py,setup.cfg,README.md,MANIFEST.in,LICENSE} src/
	cp -R ./django_trips src/

publish: _move
	python3 -m pip install --user twine
	cd src/; python3 setup.py sdist bdist_wheel; python3 -m twine upload --skip-existing --repository pypi dist/* --verbose
	@echo Warning: Do you want to delete src/ directory? [Y/n]
	@read line; if [ $$line = "n" ]; then echo aborting; exit 1 ; fi
	rm -rf src/





