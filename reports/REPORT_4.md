# REPORT 4

## Что сделано

- **Alembic:** настроен для async SQLAlchemy, первая миграция `001_initial_schema` создаёт таблицы `users`, `segments`, `funnels`, `funnel_steps`, `leads`; в `segments` включено поле `is_active`.
- **Healthcheck:** модуль `utils/healthcheck.py` — проверки БД (SELECT 1), scheduler (running + jobs), Bot API (get_me); функция `run_healthcheck()` возвращает словарь статусов.
- **Команда /health:** доступна только для `ADMIN_ID`; выводит состояние Database, Scheduler, Bot API (OK/FAIL).
- **Rate limit:** middleware ограничивает частоту сообщений пользователя (по умолчанию не более 5 сообщений за 2 секунды); при превышении — сообщение «⚠️ Слишком много запросов. Попробуйте через пару секунд.» без вызова хендлера.
- **Scheduler:** перед добавлением job проверяется `get_job(job_id)` — при существовании job пропуск; добавлено логирование «Scheduled job» и «Scheduler job failed».
- **Broadcast:** сервис `broadcast_service.send_broadcast` — рассылка с задержкой между сообщениями (`BROADCAST_DELAY`), обработка `TelegramForbiddenError`, `TelegramNotFound`, `TelegramBadRequest` без остановки цикла, подсчёт успехов и ошибок.
- **Логирование:** формат `[time] [level] [module] message`; уровни INFO, WARNING, ERROR.
- **main.py:** при старте логи «Starting LeadFunnelBot», «Connecting database», «Starting scheduler», «Bot started»; при завершении — `scheduler.shutdown()`, `engine.dispose()`, логи остановки.
- **Docker:** HEALTHCHECK с вызовом `python healthcheck_script.py`; скрипт проверяет БД и Bot API (scheduler при внешнем запуске не проверяется).
- **Config:** добавлены `RATE_LIMIT_MESSAGES`, `RATE_LIMIT_PERIOD`, `BROADCAST_DELAY`; секреты не выводятся в логах.
- **REPORT_4.md:** данный отчёт.

## Какие файлы добавлены

- **alembic.ini** — конфигурация Alembic.
- **alembic/env.py** — окружение для async SQLAlchemy, `DATABASE_URL` из config.
- **alembic/script.py.mako** — шаблон миграции.
- **alembic/versions/001_initial_schema.py** — первая миграция (users, segments, funnels, funnel_steps, leads; Segment.is_active).
- **utils/healthcheck.py** — check_database, check_scheduler, check_bot, run_healthcheck.
- **middlewares/rate_limit.py** — RateLimitMiddleware (in-memory timestamps).
- **middlewares/app_state.py** — AppStateMiddleware (session_factory, scheduler в data).
- **services/broadcast_service.py** — get_all_users_for_broadcast, send_broadcast (delay, обработка blocked/deactivated).
- **healthcheck_script.py** — скрипт для Docker HEALTHCHECK (exit 0 при OK БД и Bot API).
- **reports/REPORT_4.md** — отчёт итерации 4.

## Какие файлы изменены

- **config/config.py** — добавлены RATE_LIMIT_MESSAGES, RATE_LIMIT_PERIOD, BROADCAST_DELAY.
- **requirements.txt** — добавлен alembic.
- **main.py** — RateLimitMiddleware, AppStateMiddleware, порядок middleware; логи старта/остановки; shutdown scheduler и engine.dispose().
- **handlers/admin.py** — обработчик /health (только ADMIN_ID), использование run_healthcheck.
- **services/scheduler_service.py** — проверка существования job (skip при дубликате), logger.info при добавлении job, logger.error при ошибке.
- **services/user_service.py** — get_all_users_telegram_ids для рассылки.
- **utils/logger.py** — формат логов `[time] [level] [module] message`.
- **Dockerfile** — HEALTHCHECK CMD python healthcheck_script.py.
- **.env.example** — RATE_LIMIT_MESSAGES, RATE_LIMIT_PERIOD, BROADCAST_DELAY.

## Как реализованы миграции

- Alembic настроен в `alembic.ini`; в `alembic/env.py` используется async engine и `run_async` для генерации и применения миграций.
- `DATABASE_URL` берётся из `Config.from_env()` (без вывода в логи).
- Первая миграция `001_initial_schema` создаёт таблицы в порядке зависимостей: segments (с колонкой is_active), users, funnels, funnel_steps, leads.
- Команды: `alembic upgrade head` — применить миграции; `alembic revision --autogenerate` — создать новую миграцию по изменениям моделей.

## Как работает healthcheck

- **check_database(session_factory):** открывает сессию, выполняет `SELECT 1`, возвращает "ok" или "fail".
- **check_scheduler(scheduler):** проверяет, что scheduler не None, running, и что get_jobs() не падает; иначе "fail".
- **check_bot(bot):** вызывает `await bot.get_me()`; при успехе "ok", при исключении "fail".
- **run_healthcheck(session_factory, bot, scheduler=None):** выполняет все три проверки и возвращает dict `{ "database": "ok"|"fail", "scheduler": "ok"|"fail", "bot": "ok"|"fail" }`.
- Команда `/health` в боте доступна только для ADMIN_ID; вызывает run_healthcheck и отправляет пользователю текст с OK/FAIL по каждому компоненту.
- Скрипт `healthcheck_script.py` создаёт engine, session_factory и bot, вызывает run_healthcheck(scheduler=None); выходит с кодом 0 только если database и bot — "ok" (для Docker контейнера scheduler в отдельном процессе не проверяется).

## Как работает rate limit

- **RateLimitMiddleware:** хранит в памяти словарь `user_id → список timestamps` последних сообщений.
- Для каждого входящего Message проверяется: за последние `RATE_LIMIT_PERIOD` секунд не больше `RATE_LIMIT_MESSAGES` сообщений от этого пользователя.
- При превышении лимита отправляется ответ «⚠️ Слишком много запросов. Попробуйте через пару секунд.» и handler не вызывается.
- Старые метки времени удаляются (оставляются только в пределах окна). Callback_query не ограничиваются (только message).
- Параметры задаются в config: RATE_LIMIT_MESSAGES (по умолчанию 5), RATE_LIMIT_PERIOD (по умолчанию 2).

## Как улучшен scheduler

- Перед добавлением job проверяется `scheduler.get_job(job_id)`; если job уже существует — пропуск и запись в лог «job уже существует».
- После успешного добавления job — `logger.info("Scheduled job", job_id)`.
- При исключении при добавлении или при выполнении job — `logger.error("Scheduler job failed", ...)` / логирование ошибки отправки шага.
- Защита от дубликатов по тому же job_id сохраняется за счёт проверки и при необходимости replace_existing=True.

## Как защищена рассылка

- **send_broadcast** в `services/broadcast_service.py` получает список telegram_id через `get_all_users_for_broadcast(session)`.
- Между каждой отправкой выполняется `await asyncio.sleep(config.BROADCAST_DELAY)` (по умолчанию 0.05 сек) — снижение риска Telegram flood.
- Исключения `TelegramForbiddenError` (бот заблокирован) и `TelegramNotFound` (чат/пользователь не найден) перехватываются: логируется предупреждение, счётчик ошибок увеличивается, цикл не прерывается.
- Дополнительно обрабатывается `TelegramBadRequest`; остальные исключения логируются как error, цикл продолжается.
- Функция возвращает (total, success_count, error_count) для отчёта.

## Как проверять систему

- **Запуск бота:** `python main.py` — в логах должны появиться «Starting LeadFunnelBot», «Connecting database», «Starting scheduler», «Bot started».
- **/health:** от имени пользователя с ADMIN_ID отправить `/health` — ответ с блоком «System health» и статусами Database, Scheduler, Bot API (OK/FAIL).
- **Рассылка:** использовать сервис `send_broadcast(bot, session_factory, text)` из кода или из будущего админ-хендлера; проверить логи на предупреждения по заблокированным пользователям и задержку между отправками.
- **Смена сегмента:** пройти воронку → «Сменить направление» → выбрать другой сегмент — старые job'ы отменяются, новые планируются; в логах «Scheduled job» для новых шагов.
- **Scheduler jobs:** при выборе сегмента и шагов воронки в логах — «Scheduled job: funnel_step_<user_id>_<step_id>»; при повторном вызове — «job уже существует, пропуск».
- **Rate limit:** быстро отправить 6+ сообщений подряд от одного пользователя — после лимита должно прийти «⚠️ Слишком много запросов. Попробуйте через пару секунд.» без выполнения хендлера.
- **Docker:** собрать образ, запустить контейнер; `docker inspect` по HEALTHCHECK должен показывать выполнение `python healthcheck_script.py`; при рабочей БД и токене — healthy.

## Что делать в итерации 5

- Подключить рассылку к админке: кнопка/команда «Рассылка», ввод текста, вызов `send_broadcast` и вывод результата (total/success/errors).
- При необходимости — фильтр рассылки по сегменту (только пользователи выбранного сегмента).
- Рассмотреть вынос rate limit в Redis для многопроцессного/многопоточного окружения.
- Добавить метрики (например, счётчики сообщений, ошибок рассылки) и при необходимости экспорт в Prometheus/логи.
- Доработать тесты (pytest) на healthcheck, rate limit, broadcast (mock Bot и session).
