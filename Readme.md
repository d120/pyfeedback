# Feedback-Software
[![Test](https://github.com/d120/pyfeedback/actions/workflows/django.yml/badge.svg?branch=master)](https://github.com/d120/pyfeedback/actions/workflows/django.yml)
[![Coverage Status](https://coveralls.io/repos/github/d120/pyfeedback/badge.svg?branch=master)](https://coveralls.io/github/d120/pyfeedback?branch=master)


Pyfeedback is a web application created to assist the feedback to modules at TU Darmstadt.

It is written in Python 3 and utilizes the newest version of the django web framework.

## Requirements

To use pyfeedback the following tools have to be installed:
* Python 3.11 (including pip and venv)
* nodejs
* GNU gettext

## Preparing development environment

* Create a virtualenv with `python -m venv .venv`
* Activate the virtualenv with `source .venv/bin/activate`
* Install all requirements with `pip install -e ".[dev]"`
* Create the test database with `python src/manage.py migrate`
* Compile translations with `(cd src && django-admin compilemessages)`
* Install frontend dependencies with `npm i`
* Start the development server with `python src/manage.py runserver`

## Production
- Use `pip install .` to install dependencies.
- Docker: make sure to set `DJANGO_SETTINGS_MODULE=settings.prod` in .env
- Without docker: `gunicorn wsgi:application`

## Tests
pyfeedback is using a test driven development and tries to get to 100% coverage. Tests can be run with
```
python src/manage.py test feedback
```
Do not implement new functionality without providing a test for it.

## Settings

`src/manage.py` uses settings.dev, `src/wsgi.py` uses settings.prod

Use `python src/manage.py runserver --settings=settings.prod` to run production settings during development.


## Docker

- DJANGO_SETTINGS_MODULE: `settings.prod` or `settings.dev`. Docker uses wsgi.py, making `settings.prod` *default*.
- GUNICORN_WORKERS: *default* 3 workers
