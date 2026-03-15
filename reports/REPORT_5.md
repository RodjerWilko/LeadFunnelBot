# REPORT 5

## Что сделано

- **README.md** — описание проекта, функции, технологии, архитектура, Demo bot, установка (локально и Docker), миграции, Features (автоворонки, сегменты, админка, рассылка), переменные окружения, VPS deploy, секция Screenshots.
- **Production docker** — `docker-compose.prod.yml`: сервис `bot`, образ из текущей директории, `container_name: leadfunnelbot`, `restart: unless-stopped`, `env_file: .env`, сеть `bot-network`. Внешняя БД (postgres не в составе).
- **Deploy script** — `scripts/deploy.sh`: `git pull`, `docker compose -f docker-compose.prod.yml up -d --build`, затем `docker compose -f docker-compose.prod.yml run --rm bot alembic upgrade head`. На Unix: `chmod +x scripts/deploy.sh` перед первым запуском.
- **.gitignore** — дополнен: `.env.local`, `.env.production`, `pycache/`, `*.pyo`, `*.db`, `.vscode/`, `.idea/`.
- **Env подготовка** — `.env.example` обновлён: явно перечислены `BOT_TOKEN`, `DATABASE_URL`, `ADMIN_ID`, `RATE_LIMIT_MESSAGES`, `RATE_LIMIT_PERIOD`, `BROADCAST_DELAY` с комментариями.
- **VERSION** — файл `VERSION` с содержимым `1.0.0`.

## Как запускать проект

### Локально

```bash
pip install -r requirements.txt
cp .env.example .env
# Заполнить .env: BOT_TOKEN, DATABASE_URL, ADMIN_ID
alembic upgrade head   # при первой установке
python main.py
```

### Docker

Обычный запуск (с локальным docker-compose с БД при необходимости):

```bash
docker compose up -d --build
```

Production (внешняя БД, только бот):

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml run --rm bot alembic upgrade head
```

### VPS

```bash
git clone <repo> LeadFunnelBot
cd LeadFunnelBot
cp .env.example .env
nano .env   # BOT_TOKEN, DATABASE_URL (хост БД), ADMIN_ID
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml run --rm bot alembic upgrade head
```

## Архитектура проекта

- **config/** — конфигурация из переменных окружения (`Config.from_env()`).
- **models/** — SQLAlchemy-модели: User, Segment, Funnel, FunnelStep, Lead; Base.
- **services/** — бизнес-логика: воронки, пользователи, лиды, scheduler, админка, сегменты, рассылка.
- **handlers/** — роутеры aiogram: start, segments, funnel, lead, admin (включая /admin, /health).
- **keyboards/** — клавиатуры для сообщений и callback.
- **middlewares/** — DbSessionMiddleware, RateLimitMiddleware, AppStateMiddleware (session_factory, scheduler).
- **utils/** — логирование, healthcheck.
- **alembic/** — миграции БД (env.py async, versions/).
- **scripts/** — deploy.sh для production deploy.
- **reports/** — отчёты итераций (REPORT_1–5).

## Как работает deploy

**deploy.sh** выполняется на сервере (Linux) после клонирования/обновления репозитория:

1. **git pull** — подтягивает последние изменения.
2. **docker compose -f docker-compose.prod.yml up -d --build** — собирает образ и запускает контейнер `leadfunnelbot` в фоне с перезапуском при падении.
3. **docker compose -f docker-compose.prod.yml run --rm bot alembic upgrade head** — одноразовый запуск контейнера с командой `alembic upgrade head` (использует тот же .env и DATABASE_URL), применяет миграции и завершает контейнер.

Перед первым запуском на Unix: `chmod +x scripts/deploy.sh`.

## Как использовать бота

- **/start** — приветствие, выбор сегмента (направления), вход в воронку и получение шагов по расписанию.
- **/admin** — админ-панель (только для пользователя с `ADMIN_ID`): управление воронками, сегментами, редактирование текстов шагов, включение/выключение сегментов.
- **/health** — проверка состояния системы (только для `ADMIN_ID`): Database, Scheduler, Bot API (OK/FAIL).

Остальной сценарий: выбор сегмента → шаги воронки с кнопкой «Сменить направление» → лиды и статистика через админку.

## Что можно улучшить

- **Redis rate limit** — вынести учёт запросов в Redis для работы за несколькими инстансами бота и без потери при рестарте.
- **Celery (или иные очереди)** — вынести отложенную отправку шагов воронки и рассылку в очередь для масштабирования и повторных попыток.
- **Webhook режим** — переключение с long polling на webhook для снижения задержек и нагрузки при высокой посещаемости.
- **Prometheus метрики** — экспорт метрик (количество сообщений, ошибки рассылки, активные пользователи) для мониторинга в production.
