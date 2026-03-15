# main.py — точка входа: конфиг, БД, bootstrap, бот, scheduler, polling
from __future__ import annotations

import asyncio
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from config.config import Config
from models.base import Base
from models.lead import Lead
from models.user import User
from models.segment import Segment
from models.funnel import Funnel
from models.funnel_step import FunnelStep
from services.funnel_service import bootstrap_default_funnels
from services.scheduler_service import create_scheduler
from middlewares.db import DbSessionMiddleware
from middlewares.app_state import AppStateMiddleware
from middlewares.rate_limit import RateLimitMiddleware
from handlers.start import start_router
from handlers.segments import segments_router
from handlers.funnel import funnel_router
from handlers.lead import lead_router
from handlers.admin import router as admin_router
from utils.logger import setup_logging, get_logger

logger = get_logger(__name__)


async def create_tables(engine) -> None:
    """Создать таблицы БД."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def main() -> None:
    setup_logging()
    logger.info("Starting LeadFunnelBot")

    try:
        config = Config.from_env()
    except Exception as e:
        logger.exception("Ошибка загрузки конфига: %s", e)
        sys.exit(1)

    if not config.BOT_TOKEN:
        logger.error("BOT_TOKEN не задан")
        sys.exit(1)

    logger.info("Connecting database")
    try:
        engine = create_async_engine(
            config.DATABASE_URL,
            echo=False,
        )
        session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    except Exception as e:
        logger.exception("Ошибка подключения к БД: %s", e)
        sys.exit(1)

    try:
        await create_tables(engine)
        logger.info("Таблицы БД созданы/проверены")
    except Exception as e:
        logger.exception("Ошибка создания таблиц: %s", e)
        await engine.dispose()
        sys.exit(1)

    try:
        async with session_factory() as session:
            await bootstrap_default_funnels(session)
        logger.info("Bootstrap сегментов и воронок выполнен")
    except Exception as e:
        logger.exception("Ошибка bootstrap: %s", e)
        await engine.dispose()
        sys.exit(1)

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    dp.message.middleware(RateLimitMiddleware(config))
    dp.message.middleware(DbSessionMiddleware(session_factory))
    dp.callback_query.middleware(DbSessionMiddleware(session_factory))

    loop = asyncio.get_event_loop()
    scheduler = create_scheduler(bot, config, session_factory, loop)
    dp.message.middleware(AppStateMiddleware(session_factory, scheduler))
    dp.callback_query.middleware(AppStateMiddleware(session_factory, scheduler))

    dp.include_router(start_router)
    dp.include_router(segments_router)
    dp.include_router(funnel_router)
    dp.include_router(lead_router)
    dp.include_router(admin_router)

    try:
        scheduler.start()
        logger.info("Starting scheduler")
    except Exception as e:
        logger.exception("Ошибка запуска scheduler: %s", e)

    try:
        logger.info("Bot started")
        await dp.start_polling(bot)
    finally:
        try:
            scheduler.shutdown(wait=False)
            logger.info("Scheduler остановлен")
        except Exception as e:
            logger.exception("Ошибка остановки scheduler: %s", e)
        await bot.session.close()
        await engine.dispose()
        logger.info("Завершение работы")


if __name__ == "__main__":
    asyncio.run(main())
