# REPORT 1

## Что сделано

- **/start** — приветствие, создание/получение пользователя, показ выбора сегмента (inline-кнопки).
- **Создание пользователя в БД** — при первом заходе через `get_or_create_user`.
- **Экран выбора сегмента** — три сегмента: Маркетинг, Telegram-боты, AI (данные из БД после bootstrap).
- **Сохранение выбранного сегмента** — `update_user_segment` по выбору callback `segment:N`.
- **Создание/поиск воронки для сегмента** — одна воронка на сегмент, получаем через `get_funnel_by_segment_id`.
- **Отправка первого сообщения воронки** — сразу после выбора сегмента: подтверждение + первый шаг (delay_hours=0) новым сообщением.
- **Планирование следующих шагов** — через APScheduler: шаги с delay_hours 24 и 72 планируются с уникальным job id `funnel_step_{user_id}_{step_id}`.
- **Возможность оставить заявку** — кнопка «📩 Оставить заявку» на каждом шаге воронки, FSM ожидания текста.
- **Отправка заявки админу** — после сохранения лида в БД отправляется сообщение в ADMIN_ID с telegram_id, username, first_name, сегментом, текстом заявки, датой.
- **Базовые inline-клавиатуры** — сегменты, шаг воронки (заявка + назад), навигация «Назад» к сегментам.
- **Запуск через main.py** — загрузка конфига, создание таблиц, bootstrap, регистрация роутеров и middleware, запуск scheduler и polling.
- **Подготовка под Docker** — Dockerfile (python:3.11-slim), docker-compose.yml (сервис bot, env_file).
- **.env.example** — BOT_TOKEN, DATABASE_URL, ADMIN_ID.
- **Отчёт reports/REPORT_1.md** — данный файл.

## Какие файлы созданы

- **config/** — config.py, __init__.py
- **models/** — base.py, user.py, segment.py, funnel.py, funnel_step.py, lead.py, __init__.py
- **services/** — user_service.py, funnel_service.py, lead_service.py, scheduler_service.py, __init__.py
- **keyboards/** — main_menu.py, segments.py, funnel.py, back.py, __init__.py
- **handlers/** — start.py, segments.py, funnel.py, lead.py, __init__.py
- **middlewares/** — db.py, __init__.py
- **utils/** — logger.py, exceptions.py, __init__.py
- **reports/** — REPORT_1.md
- **Корень:** main.py, requirements.txt, Dockerfile, docker-compose.yml, .env.example

## Архитектурные решения

- **Слоёная архитектура:** config → models → services → keyboards → handlers → main. Handlers тонкие: получают session из middleware, вызывают сервисы, формируют ответ через keyboards.
- **Scheduler:** APScheduler (AsyncIOScheduler) создаётся в main.py, в сервисе хранятся глобальные ссылки на bot, session_factory и event loop. Job'ы планируются с trigger="date" и run_date = now + delay_hours. Отправка шага из job'а выполняется в потоке планировщика через `asyncio.run_coroutine_threadsafe(coro, loop)`, чтобы не блокировать основной цикл aiogram.
- **Single-message UI:** переходы по экранам через `edit_text` одного сообщения; исключения — /start (новое сообщение), ввод текста заявки (новое сообщение), уведомление админу. При ошибке edit_text (например, текст не изменился) — fallback на answer с логированием.
- **БД:** SQLAlchemy 2.0 async, одна сессия на запрос через DbSessionMiddleware. Таблицы создаются при старте; bootstrap заполняет сегменты и воронки, если их ещё нет.

## Модели БД

- **User** — id, telegram_id (unique, index), username, first_name, segment_id (FK → segments), created_at. Связи: segment, leads.
- **Segment** — id, name (unique), description, created_at. Связи: users, funnels.
- **Funnel** — id, segment_id (FK), name, created_at. Связи: segment, steps.
- **FunnelStep** — id, funnel_id (FK), step_number, delay_hours, message_text, created_at. Уникальность (funnel_id, step_number). Связь: funnel.
- **Lead** — id, user_id (FK), message, created_at. Связь: user.

## Что реализовано в handlers

- **start.py** — команда /start: get_or_create_user, get_segments, ответ с приветствием и segments_keyboard.
- **segments.py** — callback `segment:N`: сохранение segment_id, получение воронки и шагов, edit_text подтверждения, отправка первого шага, планирование шагов 2 и 3 через scheduler_service.
- **funnel.py** — callback `nav:segments`: возврат к экрану выбора сегментов через edit_text.
- **lead.py** — callback `lead:create`: переход в FSM LeadStates.waiting_message; обработка текстового сообщения: create_lead, отправка заявки админу, подтверждение пользователю, сброс FSM.

## Что реализовано в services

- **user_service** — get_user_by_telegram_id, create_user, get_or_create_user, update_user_segment.
- **funnel_service** — get_segments, get_segment_by_id, get_segment_by_name, get_funnel_by_segment_id, get_funnel_steps, bootstrap_default_funnels (сегменты Маркетинг/Telegram-боты/AI и по одной воронке из 3 шагов с delay 0/24/72 ч).
- **lead_service** — create_lead.
- **scheduler_service** — create_scheduler (с сохранением bot, session_factory, loop), schedule_funnel_steps (добавление job'ов с уникальным id), send_scheduled_funnel_step (async отправка шага пользователю), _run_send_step (обёртка для вызова из потока scheduler).

## Что не сделано

- Полноценная админка (управление сегментами/воронками через бота).
- Статистика (лиды, конверсии).
- Массовые рассылки.
- Редактирование воронок через бота.
- Экорт данных.
- Оплата.
- Webhook.
- FSM для сложных сценариев кроме ввода заявки.
- Миграции Alembic.
- Сложная авторизация.
- Отдельная веб-панель.
- Кнопка «Сменить направление» (оставлена возможность добавить позже без изменения архитектуры).

## Как запускать

**Локально:**

1. Скопировать `.env.example` в `.env`, задать BOT_TOKEN, DATABASE_URL (PostgreSQL), ADMIN_ID.
2. Установить зависимости: `pip install -r requirements.txt`.
3. Запуск из корня проекта: `python main.py` (текущая директория должна быть корнем leadfunnel-bot, чтобы импорты config, models и т.д. работали).

**Через Docker:**

1. В docker-compose.yml БД не включена — предполагается внешняя PostgreSQL (например, на хосте или в другой сети). В .env указать DATABASE_URL до доступного хоста (например, host.docker.internal или IP сервера БД).
2. `docker compose up -d --build` — сборка и запуск контейнера бота.

## Что предлагается сделать во 2 итерации

- Админ-панель в боте: просмотр лидов, базовая статистика.
- Редактирование текстов шагов воронки (или создание новых воронок) через бота или конфиг.
- Миграции Alembic для безопасного изменения схемы.
- Опционально: кнопка «Сменить направление» на шагах воронки.
- Расширение воронок: больше шагов, A/B-тесты текстов.
- Экорт лидов (CSV/Excel) по запросу админа.
