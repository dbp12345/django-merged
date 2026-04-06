#!/bin/bash
set -e

source /home/ubuntu/Project/venv/bin/activate
cd /home/ubuntu/Project/app

echo "Stopping all Celery workers..."

# Остановка всех celery воркеров (основной и throttled)
sudo systemctl stop celery
sudo systemctl stop celery-throttled
sudo systemctl stop celery-one_by_one
sleep 2

# Чистим все очереди (будет работать, если Redis общий)
echo "Purging Celery queues..."
echo "y" | celery -A core purge
redis-cli FLUSHALL

# Перезапуск всех воркеров
echo "Restarting Celery workers..."
sudo systemctl start celery
sudo systemctl start celery-throttled
sudo systemctl start celery-one_by_one

# Проверка статусов
sleep 2
systemctl is-active --quiet celery && echo "Celery active." || echo "Celery failed!"
systemctl is-active --quiet celery-throttled && echo "Celery-throttled active." || echo "Celery-throttled failed!"
systemctl is-active --quiet celery-one_by_one && echo "Сelery-one_by_one active." || echo "Сelery-one_by_one failed!"

echo "--=DONE=--"
