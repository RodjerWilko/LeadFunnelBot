# REPORT 3

## Что сделано

- **Смена направления пользователем:** на каждом шаге воронки добавлена кнопка «🔄 Сменить направление»; при нажатии пользователь возвращается к выбору сегмента; при новом выборе обновляется `segment_id`, старые job'ы воронки в scheduler отменяются, новые планируются заново.
- **Поле `Segment.is_active`:** в модель добавлено поле `is_active: bool` (default True); пользователь видит только активные сегменты; в админке можно включать/выключать сегменты.
- **Админ-панель «Воронки»:** команда `/admin` (доступ только для `ADMIN_ID`), кнопка «⚙️ Воронки» → список сегментов → экран сегмента (название, статус, Шаги, Вкл/Выкл, Назад) → список шагов воронки → детали шага (полный текст, Редактировать, Назад) → FSM редактирования текста шага → сохранение в БД.
- **Сервисы:** `admin_service.is_admin`, `segment_admin_service` (get_all_segments, get_segment_by_id_for_admin, toggle_segment_active), `funnel_admin_service` (get_funnel_steps_with_preview, get_funnel_step_by_id, update_funnel_step_text).
- **Отмена job'ов при смене направления:** `scheduler_service.cancel_user_funnel_jobs(user_id)` — находит и удаляет все job'ы с id вида `funnel_step_{user_id}_*`.

## Какие файлы созданы

- **services/admin_service.py** — проверка `is_admin(telegram_id, admin_id)`.
- **services/segment_admin_service.py** — get_all_segments, get_segment_by_id_for_admin, toggle_segment_active.
- **services/funnel_admin_service.py** — get_funnel_steps_with_preview, get_funnel_step_by_id, update_funnel_step_text (с selectinload для funnel).
- **keyboards/admin_funnels.py** — admin_menu_keyboard, admin_segments_list_keyboard, admin_segment_screen_keyboard, admin_steps_list_keyboard, admin_step_detail_keyboard.
- **states/admin_funnel.py** — AdminEditStepStates.waiting_text для FSM редактирования шага.
- **states/__init__.py** — экспорт AdminEditStepStates.
- **handlers/admin.py** — /admin, admin:back, admin:funnels, admin:seg:{id}, admin:toggle:{id}, admin:steps:{id}, admin:step:{id}, admin:edit:{id}, FSM сохранения текста шага.
- **reports/REPORT_3.md** — данный отчёт.

## Какие файлы изменены

- **models/segment.py** — добавлено поле `is_active: Mapped[bool]` (default True).
- **services/funnel_service.py** — добавлена функция `get_active_segments(session)` (только сегменты с is_active == True).
- **services/scheduler_service.py** — добавлена функция `cancel_user_funnel_jobs(user_id)`.
- **handlers/start.py** — используется `get_active_segments` вместо `get_segments`.
- **handlers/funnel.py** — при возврате к сегментам используется `get_active_segments`.
- **handlers/segments.py** — перед планированием новых шагов вызывается `cancel_user_funnel_jobs(user.id)`; проверка сегмента по id без изменения (сегмент может быть неактивным при прямом callback — тогда не показываем его в выборе, но при выборе из списка только активные).
- **keyboards/funnel.py** — в `funnel_step_keyboard()` добавлена кнопка «🔄 Сменить направление».
- **main.py** — подключён `admin_router`.

## Как реализовано управление воронками

- Вход: `/admin` → проверка `ADMIN_ID` → экран «Админ-панель» с кнопкой «⚙️ Воронки».
- «Воронки» → список всех сегментов (с эмодзи ✅/❌ по is_active), callback `admin:seg:{id}`.
- Выбор сегмента → экран сегмента: название, статус (активен/выключен), кнопки «📋 Шаги», «🔁 Вкл/Выкл», «⬅️ Назад».
- «Шаги» → список шагов воронки (step_number, delay_hours, превью текста до 50 символов), callback `admin:step:{step_id}`.
- Выбор шага → полный текст шага, кнопки «✏️ Редактировать», «⬅️ Назад».
- «Редактировать» → FSM AdminEditStepStates.waiting_text → пользователь отправляет текст → `update_funnel_step_text(session, step_id, new_text)` → подтверждение.
- «Вкл/Выкл» → `toggle_segment_active(session, segment_id)` → обновление экрана сегмента.

## Как реализовано выключение сегментов

- В модели `Segment` поле `is_active` (Boolean, default True). В админке вызов `toggle_segment_active(session, segment_id)` инвертирует значение и сохраняет в БД.
- На пользовательской стороне везде, где показывается выбор сегмента (`/start`, `nav:segments`), используется `get_active_segments(session)` — только сегменты с `is_active == True`. Выключенный сегмент не отображается в кнопках и не может быть выбран заново; уже выбранный ранее segment_id у пользователя остаётся в БД.

## Как реализована смена направления пользователем

- В клавиатуре шага воронки добавлена кнопка «🔄 Сменить направление» с callback `nav:segments`. Обработчик `nav_to_segments` (handlers/funnel.py) показывает экран выбора сегмента через `get_active_segments` и `edit_text`.
- При выборе нового сегмента (handlers/segments.py) сначала вызывается `cancel_user_funnel_jobs(user.id)`, затем `update_user_segment(session, user.id, segment_id)`, затем получаем воронку нового сегмента и планируем её шаги через `schedule_funnel_steps`. Старые отложенные сообщения для предыдущей воронки больше не отправляются.

## Как реализована отмена scheduler jobs

- В `services/scheduler_service.py` добавлена функция `cancel_user_funnel_jobs(user_id: int)`. Используется глобальный `_scheduler`. Вызывается `_scheduler.get_jobs()`, для каждого job проверяется `job.id.startswith(f"funnel_step_{user_id}_")`; при совпадении вызывается `job.remove()`. Ошибки логируются, бот не падает.

## Ограничения текущей схемы без Alembic

- **Добавление колонки `is_active`:** при первом запуске после обновления кода `Base.metadata.create_all()` не изменяет уже существующие таблицы. Если таблица `segments` уже была создана без колонки `is_active`, её не будет в БД. Необходимо вручную выполнить миграцию, например для PostgreSQL:  
  `ALTER TABLE segments ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;`  
  для SQLite:  
  `ALTER TABLE segments ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1;`  
  либо пересоздать БД (с потерей данных). Рекомендация на будущее: ввести Alembic и проводить миграции через него.

## Что делать в итерации 4

- Ввести Alembic и хранить миграции (в т.ч. для добавления `is_active` и последующих изменений схемы).
- Расширить админку: статистика по сегментам (лиды/пользователи по сегменту), ручное добавление/удаление сегментов и воронок.
- Улучшение статистики: топ сегмент по лидам, пользователи и лиды по активным/неактивным сегментам (уже заложено в ТЗ итерации 3; при наличии stats_service из итерации 2 — доработать его).
- Ограничение длины текста шага при редактировании (например, 4096 символов) и валидация перед сохранением.
