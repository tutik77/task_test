## Async Task Service

Асинхронный сервис управления задачами на FastAPI с хранением в PostgreSQL и обработкой задач через RabbitMQ.

### Возможности
- REST API для CRUD-операций над задачами
- Очередь RabbitMQ с поддержкой приоритетов и параллельных воркеров
- Детальная статусная модель и таймстемпы жизненного цикла
- Alembic-миграции, покрытие тестами (pytest + httpx)
- Контейнеризация (Dockerfile + docker-compose)

### Быстрый старт (Docker)
```bash
cp env.example .env  # при необходимости переопределите переменные
docker compose up --build -d
docker compose exec api alembic upgrade head
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
Все настройки читаются из переменных окружения (в том числе из `.env`). Ключевые параметры:

| Переменная | Назначение | Значение по умолчанию |
|-----------|------------|-----------------------|
| `DATABASE_URL` | строка подключения PostgreSQL | `postgresql+asyncpg://postgres:postgres@db:5432/tasks` |
| `RABBITMQ_URL` | URL RabbitMQ | `amqp://guest:guest@rabbitmq:5672/` |
| `RABBITMQ_QUEUE` | имя очереди | `task_queue` |
| `RABBITMQ_MAX_PRIORITY` | макс. уровень приоритета сообщений | `10` |
| `WORKER_CONCURRENCY` | параллелизм воркера | `4` |
| `WORKER_PREFETCH_COUNT` | Prefetch RabbitMQ | `4` |
| `DEFAULT_PAGE_SIZE` | размер страницы по умолчанию | `20` |
| `MAX_PAGE_SIZE` | максимальный размер страницы | `100` |

### Тестирование
```bash
pytest
```
Тесты используют in-memory SQLite и заглушку очереди, поэтому выполняются быстро и изолированно.

### API

#### Общие модели
- **Приоритеты**: `LOW`, `MEDIUM`, `HIGH`  
- **Статусы**: `NEW`, `PENDING`, `IN_PROGRESS`, `COMPLETED`, `FAILED`, `CANCELLED`

**TaskRead (ответ API)**:

```json
{
  "id": "b0d8283c-0dd0-4bb5-9f9c-8a4e9e4e85b2",
  "title": "Process report",
  "description": "Generate monthly report",
  "priority": "HIGH",
  "status": "PENDING",
  "created_at": "2025-11-18T18:40:00.123456+00:00",
  "started_at": null,
  "finished_at": null,
  "result": null,
  "error": null
}
```

#### `POST /api/v1/tasks` — создать задачу

**Тело запроса** (`application/json`):

```json
{
  "title": "Process data",
  "description": "Optional description",
  "priority": "MEDIUM"
}
```

- **title** — обязательное строковое поле, 1–255 символов
- **description** — необязательное строковое поле
- **priority** — необязательное, по умолчанию `MEDIUM`

**Пример запроса:**

```bash
curl -X POST "http://localhost:8000/api/v1/tasks" \
  -H "Content-Type: application/json" \
  -d '{"title": "Process data", "priority": "HIGH"}'
```

**Ответ `201 Created`** — объект `TaskRead` (см. выше), статус сразу будет `PENDING`.

#### `GET /api/v1/tasks` — список задач

Параметры запроса (query):

| Параметр  | Тип        | Описание                                    |
|----------|------------|---------------------------------------------|
| `status` | `TaskStatus` \| `null`   | фильтр по статусу (необяз.)         |
| `priority` | `TaskPriority` \| `null` | фильтр по приоритету (необяз.)     |
| `limit`  | int (1–100) | размер страницы (по умолчанию `DEFAULT_PAGE_SIZE`) |
| `offset` | int (>=0)   | смещение (по умолчанию `0`)                 |

**Пример:**

```bash
curl "http://localhost:8000/api/v1/tasks?status=PENDING&priority=HIGH&limit=20&offset=0"
```

**Ответ `200 OK`:**

```json
{
  "items": [ /* массив TaskRead */ ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

#### `GET /api/v1/tasks/{id}` — получить задачу

- **Параметры пути**: `id` — UUID задачи
- **Ответ `200 OK`**: объект `TaskRead`
- **Ответ `404 Not Found`**: если задача не существует

#### `DELETE /api/v1/tasks/{id}` — отменить задачу

- **Параметры пути**: `id` — UUID задачи
- **Ответ `200 OK`**: объект `TaskRead` со статусом `CANCELLED`
- **Ответ `404 Not Found`**: если задача не найдена
- **Ответ `409 Conflict`**: если задача уже в терминальном статусе (`COMPLETED`, `FAILED`, `CANCELLED`)

#### `GET /api/v1/tasks/{id}/status` — текущий статус

- **Параметры пути**: `id` — UUID задачи
- **Ответ `200 OK`**:

```json
{
  "status": "IN_PROGRESS"
}
```

- **Ответ `404 Not Found`**: если задача не найдена

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

