# DEPLOY REPORT

## GitHub

- Репозиторий: https://github.com/RodjerWilko/LeadFunnelBot
- Обновлён: коммит "Release LeadFunnelBot v1.0.0"
- В репозитории присутствуют: README.md, docker-compose.prod.yml, Dockerfile, alembic/, scripts/deploy.sh, requirements.txt, .env.example, reports/

## Сервер

- Контейнер бота: **leadfunnelbot**
- Контейнер БД (общий): **shop-bot-db-1** (PostgreSQL)
- Сеть Docker: **shop-bot_default**

## База данных

- Имя БД: **leadfunnelbot**
- Создание на VPS:
  ```bash
  docker exec -it shop-bot-db-1 psql -U shopbot -c "CREATE DATABASE leadfunnelbot;"
  ```
- Подключение из бота: `postgresql+asyncpg://shopbot:shopbot@shop-bot-db-1:5432/leadfunnelbot`

## Docker

- Файл: `docker-compose.prod.yml`
- Сеть: внешняя `shop-bot_default` (доступ к shop-bot-db-1)
- Запуск: `docker compose -f docker-compose.prod.yml up -d`
- Контейнер после запуска: **leadfunnelbot**, restart: unless-stopped

## Проверка

- **/start** — приветствие, выбор сегмента, воронка
- **/admin** — админ-панель (только для ADMIN_ID)
- **/health** — статус системы (Database, Scheduler, Bot API)

Бот: [@RWdev_LeadFunnelBot](https://t.me/RWdev_LeadFunnelBot)

## Чеклист деплоя на VPS

1. Подключиться по SSH к серверу.
2. Создать БД: `docker exec -it shop-bot-db-1 psql -U shopbot -c "CREATE DATABASE leadfunnelbot;"`
3. Клонировать или обновить репо: `git clone https://github.com/RodjerWilko/LeadFunnelBot` или `cd LeadFunnelBot && git pull`
4. Создать `.env` в корне проекта с переменными: BOT_TOKEN, DATABASE_URL=postgresql+asyncpg://shopbot:shopbot@shop-bot-db-1:5432/leadfunnelbot, ADMIN_ID=52178124, RATE_LIMIT_MESSAGES=5, RATE_LIMIT_PERIOD=2, BROADCAST_DELAY=0.05
5. Сборка: `docker compose -f docker-compose.prod.yml build`
6. Миграции: `docker compose -f docker-compose.prod.yml run --rm bot alembic upgrade head`
7. Запуск: `docker compose -f docker-compose.prod.yml up -d`
8. Проверка: `docker ps` (контейнер leadfunnelbot), `docker logs -f leadfunnelbot` (Starting LeadFunnelBot, Connecting database, Starting scheduler, Bot started)
9. В Telegram: @RWdev_LeadFunnelBot — /start, /admin, /health
10. Healthcheck: `docker inspect leadfunnelbot` — статус **healthy**
