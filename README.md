# Project Management Microservices

Стартовый каркас микросервисной системы управления проектами и задачами.

## Первый реализованный сервис

`user-service` — регистрация, авторизация, получение профиля текущего пользователя.

Стек: FastAPI, PostgreSQL, SQLAlchemy 2 async, asyncpg, JWT, Argon2, Docker Compose, uv.

## Запуск

1. Установите Docker и Docker Compose.
2. Скопируйте `.env.example` в `.env`.
3. Задайте собственный `JWT_SECRET_KEY` (например, `openssl rand -hex 32`).
4. Запустите:

```bash
docker compose up --build
```

Документация API: http://localhost:8000/docs  
Проверка состояния: http://localhost:8000/health

## Основные маршруты

- `POST /api/v1/auth/register` — регистрация.
- `POST /api/v1/auth/login` — получение JWT.
- `GET /api/v1/users/me` — профиль текущего пользователя (Bearer token).
- `GET /health` — проверка приложения и БД.

## Локальная разработка без Docker

```bash
uv sync
uv run uvicorn app.main:app --reload
```

Для локального запуска PostgreSQL должен быть доступен по адресу из `DATABASE_URL`.

## Структура

```text
.
├── app/
│   ├── api/
│   │   ├── deps.py
│   │   └── routes/
│   │       ├── auth.py
│   │       └── users.py
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   ├── db/
│   │   ├── base.py
│   │   └── session.py
│   ├── models/
│   │   └── user.py
│   ├── schemas/
│   │   └── user.py
│   ├── services/
│   │   └── auth.py
│   └── main.py
├── Dockerfile
├── compose.yaml
└── pyproject.toml
```

## Важные решения

- UUID используется как идентификатор пользователя.
- В БД хранится только хеш пароля, не исходный пароль.
- Пароли хешируются алгоритмом Argon2.
- Глобальная роль пользователя отделена от роли в проекте. Роли `MANAGER` и `MEMBER` будут храниться в контексте Project Management.
- `user-service` владеет только своей базой данных. Другие микросервисы будут хранить `user_id` как внешний идентификатор, не создавая межсервисные SQL foreign key.
- Для учебного старта таблица создаётся при запуске приложения. Перед расширением проекта подключим Alembic и миграции.
