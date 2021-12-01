include .env
backup_file := pg_$(shell date "+%Y_%m_%d_%H:%M:%S").sql.gz
compose_file := docker-compose.yml
compose := docker-compose -f $(compose_file)

build:
	$(compose) build --parallel

up_db:
	$(compose) up -d db

up: build
	$(compose) up -d

down:
	$(compose) down

makemigrations:
	$(compose) exec web python manage.py makemigrations

migrate:
	$(compose) exec web python manage.py migrate

shell:
	$(compose) exec web python manage.py shell_plus

ps:
	$(compose) ps -a $(service)

logs:
	$(compose) logs -f $(service)

remove_migrations:
	bash -c "for file in $$(find gold_crowdsale -name 000*); do sudo rm -rf $$file; done"

