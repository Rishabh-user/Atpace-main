.PHONY: all help translate test clean update compass collect rebuild

project_name = $(shell pwd)/
TEST_SETTINGS={{ project_name }}.test_settings

# target: help - Display callable targets.
help:
	@echo "ℹ️ Help"
	@egrep "^# target:" [Mm]akefile

# target: compass - compass compile all scss files
compass:
	@echo "  🧭 starting compilation of compass files! 🧭 "
	compass && compass compile
	@echo "  ✅ compass compilation done!"

# target: update - install (and update) pip requirements
install: 
	@echo " 📦 installing dependencies! 📦  "
	pip install -r requirements.txt
	@echo "  ✅ required dependencies are installed!"

# target: sync models to Database
migrate:
	@echo " 🖇️  starting migration 🖇️ "
	python manage.py makemigrations
	python manage.py migrate --run-syncdb
	@echo "  ✅ migration done!"

# target: sync models to Database
migrate3:
	@echo " 🖇️  starting migration 🖇️ "
	python manage.py makemigrations
	python manage.py migrate --run-syncdb
	@echo "  ✅ migration done!"

# target: run - calls the "runserver" django command
run:
	@echo "  🖥️  Server starting! ⌛ "
	python manage.py runserver 0.0.0.0:8000
	@echo "  ✅  Server is running!"

run3:
	@echo "  🖥️  Server starting! ⌛ "
	python manage.py runserver 0.0.0.0:8000
	@echo "  ✅  Server is running!"

# target: test - calls the "test" django command
test:
	@echo " 🧪 Start testing! 🧪 "
	python manage.py test
	@echo "  ✅ all the implemented test ran"

# target: coverage - calls the "coverage" command
coverage:
	@echo " ✔️ Start coveraging! ✔️ "
	coverage run manage.py test
	coverage report
	@echo "  ✅ coverage reported!"

# target: clean - remove all ".pyc" files
clean:
	@echo " 🧹 Start cleaning cache! 🧹 "
	python manage.py clean_pyc
	@echo "  ✅ cache cleaned!"

# target: flake8 - run flake8 
flake8:
	@echo " 🚨  Start python linting using flake8!  🚨 "
	flake8
	@echo " ✅  linting done"

# target: shell - run shell
shell:
	@echo " ⚔️  Django shell starting! ⚔️ "
	python manage.py shell
	@echo " ✅  shell running completed!"

# target: create super user - django create super user
createsuperuser:
	@echo "  👥  django create super user 👥  "
	python manage.py createsuperuser
	@echo " ✅  superuser created!"

# target: docker - run docker
docker:
	@echo "  📦️  Starting docker 📦️  "
	docker compose up
	@echo "  ✅  docker run finished"
