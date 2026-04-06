## Что делать сейчас:

1. Перезапустите docker-compose (на хосте, в обычном терминале):
   ```bash
   cd /app/docker
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
   ```

2. Cursor должен автоматически переподключиться к контейнеру (или нажмите Reload Window, если попросит).

3. В терминале Cursor (который внутри контейнера) запустите Django:
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

Теперь:
- Контейнер работает — Cursor подключен
- Django запускается вручную в терминале — ошибки видны и кликабельны
- Изменения в коде сразу видны — volume mapping работает

Проверьте, работает ли это.


# Настройка Docker для работы с Cursor

Этот документ описывает, как настроить проект для работы в Docker так, чтобы Cursor видел ошибки в коде и они были кликабельными.

## Вариант 1: Использование Remote-Containers (Рекомендуется)

Этот вариант позволяет Cursor работать напрямую внутри Docker контейнера, что обеспечивает:
- ✅ Полную поддержку автодополнения
- ✅ Кликабельные ошибки с правильными путями
- ✅ Работу линтера и проверки типов
- ✅ Отладку внутри контейнера

### Шаги:

1. **Убедитесь, что установлено расширение Remote-Containers:**
   - Откройте панель расширений (`Ctrl+Shift+X`)
   - Найдите и установите `ms-vscode-remote.remote-containers`

2. **Запустите проект:**
   ```bash
   cd docker
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
   ```

3. **Откройте проект в контейнере:**
   - Нажмите `F1` или `Ctrl+Shift+P`
   - Выберите `Remote-Containers: Reopen in Container`
   - Или нажмите на иконку Remote в левом нижнем углу Cursor

4. **Cursor автоматически подключится к контейнеру** и настроит все необходимое.

## Вариант 2: Локальная работа с Volume Mapping

Если вы предпочитаете работать локально, но с кодом в Docker:

### Шаги:

1. **Запустите проект:**
   ```bash
   cd docker
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
   ```

2. **Установите Python зависимости локально** (для работы линтера):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # или
   .venv\Scripts\activate  # Windows
   
   pip install -r requirements.txt
   ```

3. **Настройте Python интерпретатор в Cursor:**
   - Нажмите `Ctrl+Shift+P`
   - Выберите `Python: Select Interpreter`
   - Выберите интерпретатор из `.venv`

4. **Обновите `.vscode/settings.json`** для локального интерпретатора:
   ```json
   {
     "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python"
   }
   ```

## Проверка работы

После настройки проверьте:

1. **Откройте любой Python файл** (например, `core/settings.py`)
2. **Создайте намеренную ошибку** (например, добавьте несуществующий импорт)
3. **Проверьте, что:**
   - Ошибка отображается в редакторе
   - При клике на ошибку курсор переходит на нужную строку
   - В панели "Problems" (`Ctrl+Shift+M`) ошибки отображаются с правильными путями

## Решение проблем

### Ошибки не кликабельны

1. Убедитесь, что пути в контейнере (`/app`) совпадают с workspace folder
2. Проверьте, что volume правильно смонтирован:
   ```bash
   docker exec -it <container_name> ls -la /app
   ```

### Линтер не работает

1. Проверьте, что расширение Pylance установлено
2. Перезагрузите окно Cursor: `Ctrl+Shift+P` → `Developer: Reload Window`
3. Проверьте настройки в `.vscode/settings.json`

### Python интерпретатор не найден

1. В Remote-Containers: интерпретатор должен быть `/usr/local/bin/python`
2. Локально: убедитесь, что venv активирован и интерпретатор выбран

## Полезные команды

```bash
# Запуск проекта
cd docker
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Остановка проекта
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down

# Просмотр логов
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f web

# Вход в контейнер
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec web bash
```


