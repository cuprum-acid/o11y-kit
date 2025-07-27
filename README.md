# o11y-kit

Полный стек мониторинга с FastAPI приложением, PostgreSQL базой данных, Prometheus, Alertmanager и Grafana.

## 🚀 Сервисы и Порты

| Сервис | Порт | Описание |
|--------|------|----------|
| **FastAPI** | 8000 | Веб-приложение |
| **PostgreSQL** | 5432 | База данных |
| **Prometheus** | 9090 | Сбор метрик |
| **Alertmanager** | 9093 | Управление алертами |
| **Grafana** | 3000 | Визуализация и дашборды |
| **PostgreSQL Exporter** | 9187 | Экспорт метрик БД |

## 📋 API Эндпоинты

### Основные эндпоинты FastAPI

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| `GET` | `/docs` | Swagger UI |
| `GET` | `/health` | Проверка здоровья приложения |
| `GET` | `/metrics` | Метрики Prometheus |
| `GET` | `/items` | Получить все элементы |
| `POST` | `/items` | Создать новый элемент |
| `GET` | `/items/{item_id}` | Получить элемент по ID |
| `DELETE` | `/items/{item_id}` | Удалить элемент |
| `GET` | `/loadtest` | Веб-интерфейс для нагрузочного тестирования |
| `GET` | `/start-loadtest` | Запустить нагрузочное тестирование |
| `GET` | `/stop-loadtest` | Остановить нагрузочное тестирование |

### Примеры запросов

#### Создание элемента
```bash
curl -X POST "http://localhost:8000/items" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Тестовый элемент",
    "description": "Описание элемента"
  }'
```

#### Получение всех элементов
```bash
curl -X GET "http://localhost:8000/items"
```

#### Получение элемента по ID
```bash
curl -X GET "http://localhost:8000/items/1"
```

#### Удаление элемента
```bash
curl -X DELETE "http://localhost:8000/items/1"
```

#### Проверка здоровья приложения
```bash
curl -X GET "http://localhost:8000/health"
```

#### Запуск нагрузочного тестирования
```bash
curl -X GET "http://localhost:8000/start-loadtest?rps=10"
```

#### Остановка нагрузочного тестирования
```bash
curl -X GET "http://localhost:8000/stop-loadtest"
```

## 🛠️ Установка и Запуск

### 1. Клонирование и настройка
```bash
git clone 
cd 
```

### 2. Создание файла .env
```bash
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_DB=your_db_name
POSTGRES_HOST=db
POSTGRES_PORT=5432
TELEGRAM_BOT_TOKEN=7777777777:AAAAAAAAAAA-e2o_999999999AAAAAAAAA
TELEGRAM_CHAT_ID=-10000000000000
```

### 3. Отредактировать `monitoring/alertmanager/alertmanager.yml`
Изменить на свои значения
```bash
- bot_token: '7777777777:AAAAAAAAAAA-e2o_999999999AAAAAAAAA'
  chat_id: -10000000000000
```

### 3. Запуск всех сервисов
```bash
docker compose up --build -d
```

## 📊 Мониторинг и Графики

### Доступ к сервисам

- **FastAPI**: http://localhost:8000
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **Alertmanager**: http://localhost:9093

### Grafana Дашборды

1. **Вход в Grafana**:
   - URL: http://localhost:3000
   - Логин: `admin`
   - Пароль: `admin`

2. **Доступные дашборды**:
   - **FastAPI Dashboard**: Мониторинг FastAPI приложения
   - **PostgreSQL Dashboard**: Мониторинг базы данных

## 🛠 Нагрузочное тестирование

`http://localhost:8000/loadtest`

Нагрузка идёт `GET` запросом на ручку `/items`

- Ввести желаемый RPS
- Нажать кнопку `Start Test`
- Остановить тест по желанию

## 🚨 Алерты в Telegram

Алерты приходят в Telegram-канал [@AlertsKIT](https://t.me/AlertsKIT) когда RPS на /items превышает 100 в течение последней минуты

## 🏗️ Структура Проекта

```
o11y-kit/
├── src/
│   └── app/                    # Код FastAPI приложения
│       ├── main.py             # Основной файл приложения
│       ├── models.py           # Модели данных
│       └── database.py         # Настройки базы данных
├── monitoring/
│   ├── prometheus/             # Конфигурация Prometheus
│   │   ├── prometheus.yml      # Основная конфигурация
│   │   └── alerts.yml          # Правила алертов
│   ├── alertmanager/           # Конфигурация Alertmanager
│   │   └── alertmanager.yml    # Настройки уведомлений
│   └── grafana/                # Конфигурация Grafana
│       ├── dashboards/         # Дашборды
│       │   ├── fastapi-dashboard.json
│       │   └── postgres_dashboard.json
│       └── provisioning/       # Автоматическая настройка
│           ├── dashboards/
│           │   └── fastapi-dashboard.yaml
│           └── datasources/
│               └── datasource.yml
├── docker-compose.yml          # Конфигурация Docker Compose
├── Dockerfile                  # Dockerfile для FastAPI
├── requirements.txt            # Python зависимости
└── .env                       # Переменные окружения
```
