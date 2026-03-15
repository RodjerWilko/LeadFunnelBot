# LeadFunnelBot (RWdev)

Telegram-бот для автоматизации продаж через автоворонки.

## Описание

Бот позволяет сегментировать пользователей, вести их по сценариям (воронкам) с отложенной отправкой сообщений, управлять шагами из админ-панели, собирать лиды и делать массовые рассылки.

## Функции

- **Сегментация пользователей** — выбор направления/ниши при старте
- **Автоворонки сообщений** — отложенная отправка шагов по расписанию (APScheduler)
- **Scheduler** — планирование и отмена шагов при смене сегмента
- **Админ-панель** — управление воронками, сегментами, редактирование текстов шагов
- **Статистика** — просмотр лидов и активности
- **Экспорт лидов** — выгрузка данных
- **Массовая рассылка** — безопасная рассылка с задержкой и обработкой заблокированных
- **Rate limiting** — ограничение частоты запросов от пользователя
- **Healthcheck** — команда `/health` и Docker HEALTHCHECK для проверки БД, scheduler и Bot API

## Технологии

- Python 3.11
- aiogram 3
- SQLAlchemy 2 (async)
- PostgreSQL (asyncpg)
- APScheduler
- Docker
- Alembic (миграции)

## Архитектура

```
config/         — конфигурация из .env
models/         — SQLAlchemy модели (User, Segment, Funnel, FunnelStep, Lead)
services/       — бизнес-логика (воронки, рассылка, scheduler, админка)
handlers/       — обработчики команд и callback
keyboards/      — клавиатуры
middlewares/    — сессии БД, rate limit, app state
utils/          — логирование, healthcheck
alembic/        — миграции БД
```

## Demo bot

[@RWdev_LeadFunnelBot](https://t.me/RWdev_LeadFunnelBot)

## Installation

### Локальный запуск

```bash
pip install -r requirements.txt
cp .env.example .env
# Отредактируйте .env: BOT_TOKEN, DATABASE_URL, ADMIN_ID
python main.py
```

### Docker

```bash
docker compose up -d --build
```

Или для production (внешняя БД):

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

### Миграции

При первой установке или после изменений схемы:

```bash
alembic upgrade head
```

В Docker (при использовании docker-compose.prod.yml):

```bash
docker compose -f docker-compose.prod.yml run --rm bot alembic upgrade head
```

## Features

### Автоворонки

Пользователь выбирает сегмент (направление). Бот назначает воронку из шагов с задержкой (часы). Каждый шаг отправляется по расписанию; при смене сегмента старые отложенные сообщения отменяются, новые планируются заново.

### Управление сегментами

В админке можно включать/выключать сегменты (`Segment.is_active`). Пользователь видит только активные сегменты при выборе направления.

### Админ-панель

- Команда `/admin` (доступ по `ADMIN_ID`): управление воронками, список сегментов, включение/выключение, список шагов, редактирование текста шага через FSM.
- Команда `/health` — состояние системы (Database, Scheduler, Bot API).

### Рассылка

Сервис `broadcast_service.send_broadcast` — рассылка всем пользователям с задержкой между сообщениями (`BROADCAST_DELAY`), обработка заблокированных и несуществующих чатов без остановки цикла. Можно подключить к админ-кнопке или отдельной команде.

## Screenshots

_(Скриншоты интерфейса бота и админки можно добавить позже.)_

## Переменные окружения (.env)

| Переменная | Описание |
|------------|----------|
| `BOT_TOKEN` | Токен бота от @BotFather |
| `DATABASE_URL` | PostgreSQL (asyncpg), например `postgresql+asyncpg://user:pass@host:5432/dbname` |
| `ADMIN_ID` | Telegram ID администратора (число) |
| `RATE_LIMIT_MESSAGES` | Макс. сообщений на пользователя за период (по умолчанию 5) |
| `RATE_LIMIT_PERIOD` | Период в секундах (по умолчанию 2) |
| `BROADCAST_DELAY` | Задержка между сообщениями рассылки в секундах (по умолчанию 0.05) |

## VPS deploy

```bash
git clone <repo_url> LeadFunnelBot
cd LeadFunnelBot
cp .env.example .env
nano .env   # задать BOT_TOKEN, DATABASE_URL, ADMIN_ID
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml run --rm bot alembic upgrade head
```

Для обновления на сервере можно использовать скрипт (на Linux: `chmod +x scripts/deploy.sh` один раз):

```bash
./scripts/deploy.sh
```

## Лицензия

Портфолио-проект (RWdev).
