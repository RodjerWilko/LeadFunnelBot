# DB PASSWORD FIX REPORT

- **Подключение через Paramiko:** да
- **Исправленный DATABASE_URL:** `DATABASE_URL=postgresql+asyncpg://shopbot:shopbot_secret@shop-bot-db-1:5432/leadfunnelbot`
- **Запустился ли контейнер (up -d --force-recreate):** да
- **Строки в логах (Starting LeadFunnelBot, Connecting database, Starting scheduler, Bot started):** Start=True, Conn=True, Sched=True, Bot=True
- **Появились ли строки 'Bot started':** да

## Логи (последние 30 строк)

```
[2026-03-15 18:48:32] [INFO] [__main__] Starting LeadFunnelBot
[2026-03-15 18:48:32] [INFO] [__main__] Connecting database
[2026-03-15 18:48:32] [INFO] [__main__] Таблицы БД созданы/проверены
[2026-03-15 18:48:32] [INFO] [__main__] Bootstrap сегментов и воронок выполнен
[2026-03-15 18:48:33] [INFO] [apscheduler.scheduler] Scheduler started
[2026-03-15 18:48:33] [INFO] [__main__] Starting scheduler
[2026-03-15 18:48:33] [INFO] [__main__] Bot started
[2026-03-15 18:48:33] [INFO] [aiogram.dispatcher] Start polling
[2026-03-15 18:48:33] [INFO] [aiogram.dispatcher] Run polling for bot @RWdev_LeadFunnelBot id=8363305307 - 'LeadFunnelBot (RWdev)'
[2026-03-15 18:48:33] [INFO] [handlers.start] Received /start from user_id=52178124
[2026-03-15 18:48:33] [INFO] [aiogram.event] Update id=533787148 is handled. Duration 250 ms by bot id=8363305307
```
