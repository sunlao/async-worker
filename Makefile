export PYTHONPATH := $(CURDIR)/src:$(PYTHONPATH)
export PYTHONPATH := $(CURDIR)/tests:$(PYTHONPATH)

.PHONY: black lint safety
black:
	black src tests
	python -m badges.exe black
lint:
# 	execute pylint for src via badge 
	python -m badges.exe lint
# 	exeucte. pylint for tests without a badge
	pylint --rcfile=tox.ini --disable=C0103 tests
	pycodestyle src tests
	python -m badges.exe code_style
safety:
	pip-audit -r requirements.txt --strict
	bandit -r src
	sudo chown -R $$(id -u):$$(id -g) docs/code_coverage
	python -m badges.exe safety

.PHONY: up test-build test test-ci-local down
up:
	python -m scripts.reset
	docker compose -f docker-compose.yml up --build --remove-orphans --detach api db-deploy postgres redis worker
test-build:
	docker compose -f docker-compose.yml build test
test:
	docker compose -f docker-compose.yml run --no-deps --remove-orphans test tox
test-po:
	docker compose -f docker-compose.yml run --no-deps --remove-orphans test tox -e po $(arg)
test-ci-local:
	python -m scripts.reset
	docker compose -f docker-compose.yml -f docker-compose-ci-local.yml up --build --remove-orphans --detach api db-deploy postgres redis worker dbt-runtime
	docker compose -f docker-compose.yml -f docker-compose-ci-local.yml run --no-deps --rm test tox -e ci
down:
	docker compose down --remove-orphans -v
down-ci:
	docker compose down --remove-orphans -v api db-deploy postgres redis worker dbt-runtime

.PHONY: pip_runner up-ci test-ci
pip_runner:
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -r requirements-test.txt
up-ci:
	docker compose -f docker-compose.yml -f docker-compose-ci.yml pull api worker db-deploy dbt-runtime
	docker compose -f docker-compose.yml -f docker-compose-ci.yml up -d --no-build api db-deploy postgres redis worker dbt-runtime
	docker ps
test-ci:
	docker compose -f docker-compose.yml -f docker-compose-ci.yml pull test
	./scripts/path_probe.sh
	docker logs aserv-worker
	docker compose -f docker-compose.yml -f docker-compose-ci.yml run --no-deps --rm test tox -e ci
	
.PHONY: quiesce
quiesce:
	docker compose -f docker-compose.yml up --build --remove-orphans --detach quiesce