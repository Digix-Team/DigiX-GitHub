import logging

import telebot

from app.core.config import Config
from app.database.repository import Database
from app.integrations.github_api import GitHubAPI
from app.services.monitor_service import MonitorManager
from app.services.translation_service import TranslationManager


logger = logging.getLogger(__name__)


def configure_logging():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=getattr(logging, Config.LOG_LEVEL),
        handlers=[
            logging.FileHandler(Config.LOG_FILE, encoding='utf-8'),
            logging.StreamHandler(),
        ],
    )


def create_application():
    configure_logging()

    bot = telebot.TeleBot(Config.BOT_TOKEN)
    db = Database()
    github = GitHubAPI(Config.GITHUB_TOKEN)
    translation = TranslationManager()
    monitor = MonitorManager(db, github, bot)

    return {
        'bot': bot,
        'db': db,
        'github': github,
        'translation': translation,
        'monitor': monitor,
    }
