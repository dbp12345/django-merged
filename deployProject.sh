#!/bin/bash
set -eo pipefail

cd /home/ubuntu/Project/app
source /home/ubuntu/Project/venv/bin/activate

/home/ubuntu/Project/venv/bin/pip install -r requirements.txt
/home/ubuntu/Project/venv/bin/python manage.py migrate --noinput
/home/ubuntu/Project/venv/bin/python manage.py collectstatic --noinput

echo "Restarting gunicorn..."
sudo systemctl restart gunicorn || echo "gunicorn restart failed"
sudo systemctl status gunicorn --no-pager

echo "Restarting celery (default)..."
sudo systemctl restart celery || echo "Celery restart failed"

echo "Restarting celery-throttled..."
sudo systemctl restart celery-throttled || echo "celery-throttled restart failed"

echo "Restarting one_by_one..."
sudo systemctl restart celery-one_by_one || echo "one_by_one restart failed"

echo "Restarting mqtt_listener..."
sudo systemctl restart mqtt_listener || echo "mqtt_listener restart failed"

echo "Running preheatThumbnailsCommand..."
sudo -u ubuntu /home/ubuntu/Project/venv/bin/python manage.py preheatThumbnailsCommand || echo "thumbnail command failed"

echo "--= DONE =--"
