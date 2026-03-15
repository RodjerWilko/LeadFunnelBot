# DEBUG REPORT — бот не отвечает на /start

## Причина проблемы

Самая частая причина, когда бот на **long polling** не реагирует на /start:

- **У бота установлен webhook.**  
  В этом случае Telegram отправляет все обновления на URL webhook, а не в getUpdates. Контейнер с polling получает пустой поток обновлений, поэтому кажется, что бот «молчит».

Другие возможные причины:

- Контейнер не запущен или падает при старте.
- Нет доступа из контейнера к api.telegram.org (сеть Docker).
- Ошибка в обработчике /start (будет видна в логах).

## Что проверено в коде

- **main.py:** есть `await dp.start_polling(bot)`, порядок: `start_router` → segments → funnel → lead → admin. Роутер с /start подключён первым.
- **handlers/start.py:** обработчик `@router.message(CommandStart())` есть, получает `session` из `DbSessionMiddleware`.
- **middlewares:** rate limit не блокирует первое сообщение пользователя; для /start передаётся сессия БД.

Код рассчитан на **polling**; при установленном webhook обновления до бота не доходят.

## Что сделано в коде

- В обработчик /start добавлен лог: `Received /start from user_id=...`.  
  По логам можно понять: приходит ли update в приложение (появится эта строка) или проблема раньше (webhook / сеть / контейнер).

## Команды для выполнения на VPS

Подключиться по SSH и выполнить по шагам.

### 1. Проверить контейнер

```bash
docker ps
```

Должен быть контейнер **leadfunnelbot**. Если нет:

```bash
cd /path/to/LeadFunnelBot
docker compose -f docker-compose.prod.yml up -d
```

### 2. Проверить логи

```bash
docker logs leadfunnelbot --tail 100
```

Ожидаются строки: `Starting LeadFunnelBot`, `Connecting database`, `Starting scheduler`, `Bot started`.  
Если есть traceback — исправить по тексту ошибки.

### 3. Проверить и сбросить webhook (обязательно при проблеме с /start)

Узнать, установлен ли webhook (из папки проекта на сервере, где есть .env):

```bash
source .env 2>/dev/null || true
curl "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo"
```

Или подставить токен вручную вместо `${BOT_TOKEN}`.

Если в ответе поле `"url"` не пустое — бот работает через webhook, а контейнер — через polling, поэтому обновления не доходят. Удалить webhook:

```bash
source .env 2>/dev/null || true
curl "https://api.telegram.org/bot${BOT_TOKEN}/deleteWebhook"
```

Ответ `{"ok":true,"result":true}` — webhook сброшен. После этого Telegram снова отдаёт обновления в getUpdates (polling).

### 4. Проверка доступа к Telegram из контейнера

```bash
docker exec -it leadfunnelbot ping -c 2 api.telegram.org
```

Если пинг не проходит — проверить сеть Docker (в т.ч. что контейнер в нужной сети, например `shop-bot_default`).

### 5. Перезапуск контейнера (после сброса webhook)

```bash
cd /path/to/LeadFunnelBot
docker compose -f docker-compose.prod.yml up -d
```

При изменении кода перед этим:

```bash
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

### 6. Проверка получения обновлений

В одном терминале смотреть логи в реальном времени:

```bash
docker logs -f leadfunnelbot
```

В Telegram нажать /start. В логах должна появиться строка:

`Received /start from user_id=...`

Если после deleteWebhook эта строка появляется, но ответа в Telegram нет — ошибка уже в обработчике или БД (смотреть следующий traceback в логах).

## Подтверждение, что /start работает

После сброса webhook и перезапуска контейнера:

1. Открыть бота в Telegram (например @RWdev_LeadFunnelBot).
2. Отправить **/start** — бот должен ответить приветствием и клавиатурой выбора направления.
3. Проверить **/admin** (под учёткой с ADMIN_ID) и **/health**.

Если все три команды отвечают — проблема с /start устранена.

## Краткий чеклист

| Шаг | Команда / действие |
|-----|---------------------|
| 1 | `docker ps` — есть leadfunnelbot |
| 2 | `docker logs leadfunnelbot --tail 100` — нет ошибок, есть "Bot started" |
| 3 | `curl .../getWebhookInfo` — смотреть поле `url` |
| 4 | Если url не пустой — `curl .../deleteWebhook` |
| 5 | `docker compose -f docker-compose.prod.yml up -d` (при необходимости — сначала `build`) |
| 6 | В Telegram: /start, /admin, /health — бот отвечает |

Итог: в коде ошибок не найдено; наиболее вероятная причина — установленный webhook. После deleteWebhook и перезапуска контейнера /start должен заработать.
