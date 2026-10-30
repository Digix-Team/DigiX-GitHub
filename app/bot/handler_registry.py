from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.handlers.general import GeneralHandlers
from app.handlers.repositories import RepositoryHandlers
from app.handlers.monitoring import MonitoringHandlers


def create_router(bot, db, github, monitor, translation):
    router = Router(name="github_commit_monitor")

    general = GeneralHandlers(bot, db, translation)
    repositories = RepositoryHandlers(bot, db, github, translation)
    monitoring = MonitoringHandlers(bot, db, github, monitor, translation)

    @router.message(Command("start"))
    async def start_command(message: Message):
        await general.handle_start(message)

    @router.message(Command("help"))
    async def help_command(message: Message):
        await general.handle_help(message)

    @router.message(Command("language"))
    async def language_command(message: Message):
        await general.handle_language(message)

    @router.message(Command("add"))
    async def add_command(message: Message):
        await repositories.handle_add(message)

    @router.message(Command("remove"))
    async def remove_command(message: Message):
        await repositories.handle_remove(message)

    @router.message(Command("list"))
    async def list_command(message: Message):
        await repositories.handle_list(message)

    @router.message(Command("check"))
    async def check_command(message: Message):
        await monitoring.handle_check(message)

    @router.message(Command("stats"))
    async def stats_command(message: Message):
        await monitoring.handle_stats(message)

    @router.message(Command("status"))
    async def status_command(message: Message):
        await monitoring.handle_status(message)

    @router.callback_query(F.data.startswith("set_lang_"))
    async def handle_language_callback(callback: CallbackQuery):
        await general.handle_callback_query(callback)

    return router
