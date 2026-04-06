#!/bin/bash

pids=$(sudo lsof -t -i :8000)

if [ -n "$pids" ]; then
  echo "Killing processes on port 8000: $pids"
  sudo kill $pids
else
  echo "No processes found on port 8000."
fi

source /home/ubuntu/Project/venv/bin/activate
cd /home/ubuntu/Project/app
/home/ubuntu/Project/venv/bin/pip install -r /home/ubuntu/Project/app/requirements.txt
#/home/ubuntu/Project/venv/bin/python /home/ubuntu/Project/app/manage.py makemigrations
#echo "y" | /home/ubuntu/Project/venv/bin/python /home/ubuntu/Project/app/manage.py migrate
/home/ubuntu/Project/venv/bin/python /home/ubuntu/Project/app/manage.py migrate --noinput
#echo "yes" | /home/ubuntu/Project/venv/bin/python /home/ubuntu/Project/app/manage.py collectstatic
/home/ubuntu/Project/venv/bin/python /home/ubuntu/Project/app/manage.py collectstatic --noinput
nohup gunicorn --workers 3 core.wsgi:application  > /home/ubuntu/Project/app/logs/gunicorn.log 2>&1 &
echo "Gunicorn started."

sudo systemctl restart celery --no-block
if [ $? -eq 0 ]; then
  echo "Celery restarted successfully."
else
  echo "Failed to restart Celery."
fi

sudo systemctl restart mqtt_listener
if [ $? -eq 0 ]; then
  echo "mqtt_listener restarted successfully."
else
  echo "Failed to restart mqtt_listener."
fi

echo "--=DONE=--"
