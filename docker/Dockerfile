FROM python:3.13-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

# системные либы для mysqlclient/lxml/Pillow/graphviz
RUN apt-get update && apt-get install -y --no-install-recommends mc nano \
      build-essential pkg-config \
      default-libmysqlclient-dev \
      libjpeg62-turbo zlib1g libxml2 libxslt1.1 graphviz \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
# RUN pip install --upgrade pip && pip install -r /app/requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel \
 && python -m pip install -r /app/requirements.txt

# единая, явная установка зависимостей и проверка
RUN python -m pip install --upgrade pip \
 && python -m pip install --no-cache-dir -r /app/requirements.txt \
 && python -m pip check
# debug tool
#RUN python -m pip install debugpy

# код приложения (в деве перекроется volume’ом)
COPY . /app

# entrypoint
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash","-lc","python manage.py runserver 0.0.0.0:8000"]
