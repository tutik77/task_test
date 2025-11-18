## Async Task Service

Асинхронный сервис управления задачами на FastAPI с хранением в PostgreSQL и обработкой задач через RabbitMQ.

### Возможности
- REST API для CRUD-операций над задачами
- Очередь RabbitMQ с поддержкой приоритетов и параллельных воркеров
- Детальная статусная модель и таймстемпы жизненного цикла
- Alembic-миграции, покрытие тестами (pytest + httpx)
- Контейнеризация (Dockerfile + docker-compose)

### Быстрый старт
```bash
cp env.example .env  # при необходимости переопределите переменные
docker compose up --build
```

Сервисы:
- API: http://localhost:8000 (Swagger доступен по `/docs`)
- PostgreSQL: localhost:5432
- RabbitMQ Management UI: http://localhost:15672 (guest/guest)

### Локальный запуск без Docker
1. Создайте виртуальное окружение и установите зависимости:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # или source venv/bin/activate
   pip install -r requirements.txt
   pip install -e .[dev]
   ```
2. Примените миграции:
   ```bash
   alembic upgrade head
   ```
3. Запустите API и воркер в отдельных терминалах:
   ```bash
   uvicorn app.main:app --reload
   python -m app.workers.runner
   ```

### Конфигурация
Все настройки читаются из переменных окружения с префиксом `APP_`. Ключевые параметры:

| Переменная | Назначение | Значение по умолчанию |
|-----------|------------|-----------------------|
| `APP_DATABASE_URL` | строка подключения PostgreSQL | `postgresql+asyncpg://postgres:postgres@db:5432/tasks` |
| `APP_RABBITMQ_URL` | URL RabbitMQ | `amqp://guest:guest@rabbitmq:5672/` |
| `APP_RABBITMQ_QUEUE` | имя очереди | `task_queue` |
| `APP_RABBITMQ_MAX_PRIORITY` | макс. уровень приоритета сообщений | `10` |
| `APP_WORKER_CONCURRENCY` | параллелизм воркера | `4` |
| `APP_WORKER_PREFETCH_COUNT` | Prefetch RabbitMQ | `4` |

### Тестирование
```bash
pytest
```
Тесты используют in-memory SQLite и заглушку очереди, поэтому выполняются быстро и изолированно.

### API
- `POST /api/v1/tasks` — создать задачу
- `GET /api/v1/tasks` — список задач с фильтрами `status`, `priority`, пагинация `limit/offset`
- `GET /api/v1/tasks/{id}` — получить задачу
- `DELETE /api/v1/tasks/{id}` — отменить задачу (кроме завершённых)
- `GET /api/v1/tasks/{id}/status` — текущий статус

### Архитектура
- `app/api` — FastAPI роуты и зависимости
- `app/core` — конфигурация
- `app/db` — сессии SQLAlchemy (async)
- `app/models` — ORM-модели
- `app/repositories` — слой работы с БД
- `app/services` — бизнес-логика API и воркера
- `app/mq` — интеграция с RabbitMQ
- `app/workers` — воркер и процессор задач
- `tests` — unit и интеграционные тесты

### Миграции
```bash
alembic revision --autogenerate -m "message"
alembic upgrade head
```

