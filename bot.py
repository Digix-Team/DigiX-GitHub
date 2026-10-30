import asyncio
import logging

from aiogram import Dispatcher

from app.bot.handler_registry import create_router
from app.bot.instance import create_application
from app.core.config import Config


logger = logging.getLogger(__name__)


async def main():
    application = create_application()
    bot = application["bot"]
    github = application["github"]
    monitor = application["monitor"]

    dispatcher = Dispatcher()
    dispatcher.include_router(
        create_router(**application)
    )

    logger.info("=" * 50)
    logger.info("Starting GitHub Commit Monitor Bot")
    logger.info("=" * 50)

    try:
        logger.info("Testing GitHub API connection...")
        connected = await asyncio.to_thread(github.test_connection)

        if not connected:
            logger.error("GitHub API connection failed. Check your token.")
            return

        logger.info("GitHub API connection successful")

        await monitor.start_monitoring()
        logger.info(
            "Monitoring started with %s second interval",
            Config.CHECK_INTERVAL,
        )

        logger.info("Starting Telegram polling...")
        await dispatcher.start_polling(bot)

    except Exception:
        logger.exception("Bot runtime error")

    finally:
        await monitor.stop_monitoring()
        await bot.session.close()
        logger.info("Bot shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
