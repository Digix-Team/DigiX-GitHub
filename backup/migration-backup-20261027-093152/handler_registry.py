from telebot.types import Message

from app.handlers.general import GeneralHandlers
from app.handlers.repositories import RepositoryHandlers
from app.handlers.monitoring import MonitoringHandlers


class BotHandler:
    def __init__(self, bot, db, github, monitor, translation):
        self.bot = bot

        self.general = GeneralHandlers(bot, db, translation)
        self.repositories = RepositoryHandlers(bot, db, github, translation)
        self.monitoring = MonitoringHandlers(
            bot, db, github, monitor, translation
        )

        self.register_handlers()

    def register_handlers(self):
        @self.bot.message_handler(commands=['start'])
        def start_command(message: Message):
            self.general.handle_start(message)

        @self.bot.message_handler(commands=['help'])
        def help_command(message: Message):
            self.general.handle_help(message)

        @self.bot.message_handler(commands=['language'])
        def language_command(message: Message):
            self.general.handle_language(message)

        @self.bot.message_handler(commands=['add'])
        def add_command(message: Message):
            self.repositories.handle_add(message)

        @self.bot.message_handler(commands=['remove'])
        def remove_command(message: Message):
            self.repositories.handle_remove(message)

        @self.bot.message_handler(commands=['list'])
        def list_command(message: Message):
            self.repositories.handle_list(message)

        @self.bot.message_handler(commands=['check'])
        def check_command(message: Message):
            self.monitoring.handle_check(message)

        @self.bot.message_handler(commands=['stats'])
        def stats_command(message: Message):
            self.monitoring.handle_stats(message)

        @self.bot.message_handler(commands=['status'])
        def status_command(message: Message):
            self.monitoring.handle_status(message)

        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_callback(call):
            self.general.handle_callback_query(call)
