# LeadFunnelBot

Telegram бот для автоматизации продаж через автоворонки.

**Demo:** [@RWdev_LeadFunnelBot](https://t.me/RWdev_LeadFunnelBot)

---

## Features

- сегментация пользователей  
- автоворонки сообщений  
- серия сообщений по расписанию  
- сбор заявок от клиентов  
- админ-панель  
- редактирование сценариев  
- массовая рассылка  
- статистика  
- rate limiting  
- healthcheck  

---

## Use cases

Этот бот подходит для:

- онлайн-курсов  
- инфобизнеса  
- маркетинговых воронок  
- услуг и агентств  
- продаж через Telegram  

---

## Architecture

**Структура проекта:**

- `config` — конфигурация из .env  
- `models` — сущности БД (User, Segment, Funnel, FunnelStep, Lead)  
- `services` — бизнес-логика (воронки, рассылка, scheduler, UI)  
- `handlers` — обработчики команд и callback  
- `middlewares` — сессии БД, rate limit, app state  
- `scheduler` — отложенная отправка шагов воронки (APScheduler)  
- `alembic` — миграции БД  

**Технологии:**

- Python 3.11  
- Aiogram 3  
- PostgreSQL  
- SQLAlchemy 2  
- APScheduler  
- Docker  

---

## Installation

**Локальный запуск:**

```bash
pip install -r requirements.txt
cp .env.example .env
python main.py
```

**Docker:**

```bash
docker compose up -d --build
```

**Миграции:**

```bash
alembic upgrade head
```

---

## Deploy

Deploy на сервер:

```bash
git clone https://github.com/RodjerWilko/LeadFunnelBot.git
cd LeadFunnelBot
cp .env.example .env
# Заполнить .env: BOT_TOKEN, DATABASE_URL, ADMIN_ID
docker compose -f docker-compose.prod.yml up -d
```

При первой установке применить миграции:

```bash
docker compose -f docker-compose.prod.yml run --rm bot alembic upgrade head
```

---

## Screenshots

_(Скриншоты можно добавить позже. Папка для размещения: `docs/screenshots/` — funnel.png, admin.png.)_

---

## Переменные окружения

| Переменная | Описание |
|------------|----------|
| `BOT_TOKEN` | Токен бота от @BotFather |
| `DATABASE_URL` | PostgreSQL (asyncpg) |
| `ADMIN_ID` | Telegram ID администратора |
| `RATE_LIMIT_MESSAGES` / `RATE_LIMIT_PERIOD` | Ограничение частоты запросов |
| `BROADCAST_DELAY` | Задержка между сообщениями рассылки |

---

Портфолио-проект · RWdev
