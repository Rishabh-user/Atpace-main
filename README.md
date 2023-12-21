# Atpace Web Application

## Setup

[![forthebadge made-with-python](http://ForTheBadge.com/images/badges/made-with-python.svg)](https://www.python.org/)


The first thing to do is to clone the repository:

```sh
$ git clone https://github.com/prashantk794/ravinsight.git
$ cd ravinsight
```

Create a virtual environment to install dependencies in and activate it:

```sh
$ virtualenv2 --no-site-packages env
$ source env/bin/activate
```

Then install the dependencies:

```sh
(env)$ pip install -r requirements.txt
# or
(env)$ make install
```
After that make migration using command.
```sh
(env)$ python manage.py makemigrations
(env)$ python manage.py migrate --run-syncdb
# or
(env)$ make migration
```
---

Also you can use docker, First make sure you have docker installed. Then run 

```sh 
(env)$ docker compose up
# or 
(env)$ make docker
```

> ***NOTE**

Note the `(env)` in front of the prompt. This indicates that this terminal
session operates in a virtual environment set up by `virtualenv2`.
you can also use conda or venv.

`make` is only available for unix based system. 

---

Once `pip` has finished downloading the dependencies:
```sh
(env)$ cd project
# generate SECRECT_KEY before using the project.
(env)$ python manage.py runserver
```
And navigate to `http://127.0.0.1:8000/`.
Run and start using app.

## Tests Coverage report

To run the tests and get the coverage report, `cd` into the directory where `manage.py` is:
```sh
(env)$ coverage run manage.py test
# or
(env)$ make coverage
```

## Flake8

To check code is pep8 styled use flake8, `cd` into the root directory where `Makefile` located:
```sh
(env)$ make flake8
# or
(env)$ flake8
```

## TODO

- [x] User management 
- [x] Content management
- [x] Survey management
- [x] Change DB to Mysql
- [x] CI github action
- [ ] Tests
# Atpace-main
