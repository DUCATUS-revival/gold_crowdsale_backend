include .env
compose_file := docker-compose.yml
compose_file_kibana := docker-compose.elk.yml
compose := docker-compose -f $(compose_file)
compose_kibana := docker-compose -f $(compose_file_kibana)

build:
	$(compose) build --parallel

up_db:
	$(compose) up -d db

up: build
	$(compose) up -d

down:
	$(compose) down

up_kibana:
	$(compose_kibana) up -d

down_kibana:
	$(compose_kibana) down

make_all_migrations:
	$(compose) exec web python manage.py makemigrations payments purchases rates transfers api_auth withdrawals

migrate_all:
	$(compose) exec web python manage.py migrate

shell:
	$(compose) exec web python manage.py shell_plus

ps:
	$(compose) ps -a $(service)

ps_kibana:
	$(compose_kibana) ps -a $(service)

logs:
	$(compose) logs -f $(service)

remove_migrations:
	bash -c "for file in $$(find gold_crowdsale -name 000*); do sudo rm -rf $$file; done"

withdraw_btc:
	$(compose) exec web python manage.py withdraw_btc_funds

withdraw_eth:
	$(compose) exec web python manage.py withdraw_eth_funds

fix_filebeat_permissions:
	sudo chown root:root filebeat.yml
	sudo chmod 644 filebeat.yml

prepare_elastic:
	mkdir -p .docker/elasticsearch_data
	sudo chown -R 1000:1000 .docker/elasticsearch_data
