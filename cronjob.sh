#!/bin/bash

cd `dirname $0`/src
python manage.py cleanup
python manage.py cleanup_email_change_req
sqlite3 ../db/feedback.db vacuum
