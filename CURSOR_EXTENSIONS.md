# Установленные расширения для Cursor

> **Примечание:** Этот файл содержит список реально установленных расширений. При изменении списка расширений обновите также `.devcontainer/devcontainer.json`.

## Python

- **Python** (`ms-python.python`)
  - Поддержка Python, отладка, линтер
  - Автор: Microsoft
  
- **Pylance** (`ms-python.vscode-pylance`)
  - Автодополнение, проверка типов
  - Автор: Microsoft
  
- **debugpy** (`ms-python.debugpy`)
  - Отладчик для Python
  - Автор: Microsoft
  
- **Black Formatter** (`ms-python.black-formatter`)
  - Форматирование Python кода
  - Автор: Microsoft
  
- **isort** (`ms-python.isort`)
  - Сортировка импортов Python
  - Автор: Microsoft
  
- **Flake8** (`ms-python.flake8`)
  - Линтер для Python
  - Автор: Microsoft

## Django

- **Django** (`batisteo.vscode-django`)
  - Поддержка Django шаблонов, тегов
  - Автор: Baptiste Darthenay
  
- **Jinja** (`wholroyd.jinja`)
  - Поддержка Jinja2 шаблонов (используется в Django)
  - Автор: wholroyd

## CSS/HTML

- **HTML CSS Support** (`ecmel.vscode-html-css`)
  - Автодополнение CSS классов
  - Автор: ecmel
  
- **CSS Peek** (`pranaygp.vscode-css-peek`)
  - Быстрый переход к определению CSS
  - Автор: Pranay Prakash
  
- **IntelliSense for CSS class names** (`zignd.html-css-class-completion`)
  - Автодополнение CSS классов в HTML
  - Автор: Zignd

## Docker/Контейнеры

- **Docker** (`ms-azuretools.vscode-docker`)
  - Управление Docker контейнерами
  - Автор: Microsoft
  
- **Dev Containers** (`ms-azuretools.vscode-containers`)
  - Работа с dev containers
  - Автор: Microsoft

## База данных

- **SQLTools** (`mtxr.sqltools`)
  - Универсальный инструмент для работы с БД
  - Автор: Matheus Teixeira
  
- **SQLTools MySQL** (`mtxr.sqltools-driver-mysql`)
  - Драйвер MySQL для SQLTools
  - Автор: Matheus Teixeira
  
- **SQLTools PostgreSQL** (`mtxr.sqltools-driver-pg`)
  - Драйвер PostgreSQL для SQLTools
  - Автор: Matheus Teixeira
  
- **MySQL Client** (`cweijan.vscode-mysql-client2`)
  - Прямое редактирование данных (до 3 баз бесплатно)
  - Автор: cweijan
  
- **DB Client JDBC** (`cweijan.dbclient-jdbc`)
  - JDBC клиент для работы с БД
  - Автор: cweijan

## Линтинг и форматирование

- **Ruff** (`charliermarsh.ruff`)
  - Быстрый линтер для Python
  - Автор: Astral Software
  
- **ESLint** (`dbaeumer.vscode-eslint`)
  - Линтинг JavaScript
  - Автор: Microsoft
  
- **Prettier** (`esbenp.prettier-vscode`)
  - Форматирование CSS/JS/HTML
  - Автор: Prettier

## Git

- **GitLens** (`eamodio.gitlens`)
  - Расширенная работа с Git
  - Автор: GitKraken

## YAML/Markdown

- **YAML** (`redhat.vscode-yaml`)
  - Поддержка YAML (для docker-compose.yml)
  - Автор: Red Hat
  
- **Markdownlint** (`davidanson.vscode-markdownlint`)
  - Линтинг Markdown файлов
  - Автор: David Anson

## Утилиты

- **Bookmarks** (`alefragnani.bookmarks`)
  - Закладки в коде
  - Автор: Alessandro Fragnani
  
- **Default Keybindings** (`jbro.vscode-default-keybindings`)
  - Стандартные горячие клавиши
  - Автор: jbro

## Cursor-специфичные (не устанавливаются в devcontainer)

- **CursorPyright** (`anysphere.cursorpyright`)
  - Встроенный анализатор типов для Cursor
  
- **Remote Containers** (`anysphere.remote-containers`)
  - Поддержка dev containers в Cursor
  
- **Remote SSH** (`anysphere.remote-ssh`)
  - Подключение к удаленным серверам через SSH

## Темы (не устанавливаются в devcontainer)

- **Night Coder** (`a5hk.night-coder`)
- **Backspace Theme** (`samiurrahmanmukul.backspace-theme`)
- **Theme Maple** (`subframe7536.theme-maple`)
- **Gerry Themes** (`local.gerry-themes`) - локальная тема

---

## Быстрая установка через командную строку

```bash
# Python
cursor --install-extension ms-python.python
cursor --install-extension ms-python.vscode-pylance
cursor --install-extension ms-python.debugpy
cursor --install-extension ms-python.black-formatter
cursor --install-extension ms-python.isort
cursor --install-extension ms-python.flake8

# Django
cursor --install-extension batisteo.vscode-django
cursor --install-extension wholroyd.jinja

# CSS
cursor --install-extension ecmel.vscode-html-css
cursor --install-extension pranaygp.vscode-css-peek
cursor --install-extension zignd.html-css-class-completion

# Docker
cursor --install-extension ms-azuretools.vscode-docker
cursor --install-extension ms-azuretools.vscode-containers

# База данных
cursor --install-extension mtxr.sqltools
cursor --install-extension mtxr.sqltools-driver-mysql
cursor --install-extension mtxr.sqltools-driver-pg
cursor --install-extension cweijan.vscode-mysql-client2
cursor --install-extension cweijan.dbclient-jdbc

# Линтинг и форматирование
cursor --install-extension charliermarsh.ruff
cursor --install-extension dbaeumer.vscode-eslint
cursor --install-extension esbenp.prettier-vscode

# Git
cursor --install-extension eamodio.gitlens

# YAML/Markdown
cursor --install-extension redhat.vscode-yaml
cursor --install-extension davidanson.vscode-markdownlint

# Утилиты
cursor --install-extension alefragnani.bookmarks
cursor --install-extension jbro.vscode-default-keybindings
```

---

## Настройки для проекта

После установки расширений, создайте `.vscode/settings.json` с настройками:

```json
{
  // Python
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  
  // Django
  "files.associations": {
    "**/*.html": "django-html",
    "**/templates/**/*.html": "django-html",
    "**/templates/**": "django-txt",
    "**/requirements{/**,*}.{txt,in}": "pip-requirements"
  },
  "emmet.includeLanguages": {
    "django-html": "html"
  },
  
  // CSS
  "css.validate": true,
  "css.lint.unknownAtRules": "ignore",
  
  // Docker
  "docker.showStartPage": false,
  
  // Editor
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```
