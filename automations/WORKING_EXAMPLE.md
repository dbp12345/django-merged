# Рабочий пример использования системы автоматизации

## Шаг 1: Создание автоматизации через админ-панель

1. Войдите в Django Admin панель
2. Перейдите в раздел **Automations** → **Automations**
3. Нажмите **Add Automation**

## Шаг 2: Пример 1 - Автоматическое обновление времени модификации при изменении статуса сотрудника

### Настройки автоматизации:

- **Name:** `Обновление времени модификации при смене статуса`
- **Is active:** ✓ (включено)
- **Trigger model:** `company.Employees`
- **Trigger field:** `status_code`
- **Trigger type:** `field_changed`
- **Action type:** `code`
- **Action code:**
```python
# Обновляем время последней модификации при изменении статуса сотрудника
from datetime import datetime
instance.last_modified_time = datetime.now()
```

### Как это работает:

1. Когда у сотрудника (модель `company.Employees`) изменяется поле `status_code`
2. Система автоматически выполняет код
3. Код обновляет поле `last_modified_time` текущим временем
4. Изменения сохраняются автоматически

### Тестирование:

1. Откройте любого сотрудника в админке (`company.Employees`)
2. Измените поле `status_code` (например, с 0 на 1)
3. Сохраните
4. Проверьте, что `last_modified_time` обновился
5. Проверьте логи в **Automations** → **Automation Logs** - должна быть запись об успешном выполнении

## Шаг 3: Пример 2 - Уведомление при создании нового сотрудника через вебхук

### Настройки автоматизации:

- **Name:** `Уведомление о новом сотруднике`
- **Is active:** ✓ (включено)
- **Trigger model:** `company.Employees`
- **Trigger field:** (оставить пустым)
- **Trigger type:** `created`
- **Action type:** `webhook`
- **Webhook URL:** `https://your-api.example.com/webhooks/new-employee`

### Как это работает:

1. При создании нового сотрудника (модель `company.Employees`)
2. Система автоматически отправляет POST запрос на указанный URL
3. В теле запроса будет JSON:
```json
{
    "automation_name": "Уведомление о новом сотруднике",
    "trigger_field": null,
    "old_value": null,
    "new_value": null,
    "object_id": 123,
    "model": "company.Employees"
}
```

### Тестирование:

1. Создайте нового сотрудника в админке
2. Проверьте, что POST запрос был отправлен на ваш вебхук
3. Проверьте логи в **Automations** → **Automation Logs**

## Шаг 4: Пример 3 - Сложная логика с проверкой условий

### Настройки автоматизации:

- **Name:** `Автоматическая установка статуса при смене email`
- **Is active:** ✓ (включено)
- **Trigger model:** `company.Employees`
- **Trigger field:** `email`
- **Trigger type:** `field_changed`
- **Action type:** `code`
- **Action code:**
```python
# Если email изменился, устанавливаем статус "In Progress"
if new_value and new_value != old_value:
    # StatusCode.IN_PROGRESS = 1
    instance.status_code = 1
    # Также обновляем время модификации
    from datetime import datetime
    instance.last_modified_time = datetime.now()
```

### Как это работает:

1. Когда у сотрудника изменяется email
2. Проверяется, что новое значение отличается от старого
3. Автоматически устанавливается статус "In Progress" (код 1)
4. Обновляется время последней модификации

## Шаг 5: Пример 4 - Работа с параметрами сотрудника

### Настройки автоматизации:

- **Name:** `Обновление времени синхронизации параметров`
- **Is active:** ✓ (включено)
- **Trigger model:** `company.Employees_Parameters`
- **Trigger field:** `value`
- **Trigger type:** `field_changed`
- **Action type:** `code`
- **Action code:**
```python
# Обновляем время синхронизации при изменении значения параметра
from datetime import datetime
instance.sync_updated_at = datetime.now()
```

## Шаг 6: Пример 5 - Уведомление при удалении компании

### Настройки автоматизации:

- **Name:** `Уведомление об удалении компании`
- **Is active:** ✓ (включено)
- **Trigger model:** `company.Company`
- **Trigger field:** (оставить пустым)
- **Trigger type:** `deleted`
- **Action type:** `webhook`
- **Webhook URL:** `https://your-api.example.com/webhooks/company-deleted`

### Как это работает:

1. При удалении компании из базы данных
2. Система отправляет POST запрос на вебхук
3. В запросе будет информация об удаленной компании

## Просмотр логов выполнения

Все выполнения автоматизаций логируются в **Automations** → **Automation Logs**:

- **Automation** - какая автоматизация выполнилась
- **Model label** - какая модель вызвала автоматизацию (например, `company.Employees`)
- **Object ID** - ID объекта, который вызвал автоматизацию
- **Executed at** - время выполнения
- **Success** - успешно ли выполнилась автоматизация
- **Error message** - сообщение об ошибке (если была)

## Отладка проблем

Если автоматизация не работает:

1. Проверьте, что **Is active** = ✓ (включено)
2. Проверьте правильность названия модели в формате `app_label.ModelName`
3. Проверьте правильность названия поля (должно точно совпадать с полем в модели)
4. Проверьте логи в **Automation Logs** - там будет информация об ошибках
5. Убедитесь, что код синтаксически правильный

## Доступные переменные в коде

При написании кода действия доступны:

- `instance` - экземпляр модели (например, объект `Employees`)
- `old_value` - старое значение поля (None для новых записей)
- `new_value` - новое значение поля
- `date` - модуль date из datetime
- `datetime` - модуль datetime
- `models` - django.db.models для работы с моделями Django

## Примеры использования переменных

```python
# Доступ к полям экземпляра
instance.email
instance.status_code
instance.last_modified_time

# Работа с датами
from datetime import datetime
instance.last_modified_time = datetime.now()

# Работа с моделями Django
from models import Employees
all_employees = Employees.objects.all()

# Проверка условий
if new_value == 1:
    instance.status_code = 2
```
