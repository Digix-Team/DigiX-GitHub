import atexit
import logging

from app.bot.handler_registry import BotHandler
from app.bot.instance import create_application
from app.core.config import Config


logger = logging.getLogger(__name__)


def main():
    application = create_application()
    bot = application["bot"]
    github = application["github"]
    monitor = application["monitor"]

    logger.info("=" * 50)
    logger.info("Starting GitHub Commit Monitor Bot")
    logger.info("=" * 50)

    logger.info("Testing GitHub API connection...")
    if not github.test_connection():
        logger.error("❌ GitHub API connection failed! Check your token.")
        return

    logger.info("✅ GitHub API connection successful")

    BotHandler(**application)

    monitor.start_monitoring()
    logger.info(
        "✅ Monitoring started with %s second interval",
        Config.CHECK_INTERVAL,
    )

    def shutdown_handler():
        monitor.stop_monitoring()
        logger.info("🛑 Bot is shutting down...")

    atexit.register(shutdown_handler)

    logger.info("🤖 Starting Telegram bot...")

    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception:
        logger.exception("Bot polling error")


if __name__ == "__main__":
    main()
