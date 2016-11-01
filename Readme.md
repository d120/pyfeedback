# Feedback-Software
[![Build Status](https://travis-ci.org/d120/pyfeedback.svg?branch=master)](https://travis-ci.org/d120/pyfeedback)
[![Coverage Status](https://coveralls.io/repos/github/d120/pyfeedback/badge.svg?branch=master)](https://coveralls.io/github/d120/pyfeedback?branch=master)


Pyfeedback is a web application created to assist the feedback to modules at TU Darmstadt.

It is written in Python 2.7 and utilizes the newest version of the django web framework.

## Requierements

To use pyfeedback the following tools have to be installed:
* pip and virtualenv for python 2
* texlive + texlive-lang-german (to generate letters)
* [latex tuddesign](http://exp1.fkp.physik.tu-darmstadt.de/tuddesign/)

## Preparing development environment
* Create a virtualenv with virtualenv $name
* Activate the virtualenv with `source $name/bin/activate`
* Install all requierements with `pip install -r requierements.txt`
* Create the test database with `python src/manage.py migrate`
* Start the development server with `python src/manage.py runserver`

## Tests
pyfeedback is using a test driven development and tries to get to 100% coverage. Tests can be run with
```
python src/manage.py test feedback
```
Do not implement new functionality without providing a test for it.

