#!/bin/bash

cd `dirname $0`/src
python manage.py cleanup
sqlite3 ../db/feedback.db vacuum
