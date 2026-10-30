import logging

from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.enums import ParseMode

from app.core.config import Config
from app.database.repository import Database
from app.integrations.github_api import GitHubAPI
from app.services.monitor_service import MonitorManager
from app.services.translation_service import TranslationManager


logger = logging.getLogger(__name__)


def configure_logging():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO),
        handlers=[
            logging.FileHandler(Config.LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def create_application():
    configure_logging()

    session = AiohttpSession(
        api=TelegramAPIServer.from_base("https://tapi.bale.ai")
    )
    bot = Bot(
        token=Config.BOT_TOKEN,
        session=session,
        parse_mode=ParseMode.MARKDOWN,
    )
    db = Database()
    github = GitHubAPI(Config.GITHUB_TOKEN)
    translation = TranslationManager()
    monitor = MonitorManager(db, github, bot, translation)

    return {
        "bot": bot,
        "db": db,
        "github": github,
        "translation": translation,
        "monitor": monitor,
    }
