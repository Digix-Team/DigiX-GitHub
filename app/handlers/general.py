import asyncio

from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from app.core.config import Config
from app.handlers.common import CommonHandlers


class GeneralHandlers(CommonHandlers):
    def __init__(self, bot, db, translation):
        super().__init__(db)
        self.bot = bot
        self.translation = translation

    async def handle_start(self, message: Message):
        chat_id = message.chat.id
        if not self.check_admin(message.from_user.id if message.from_user else None):
            return

        username = message.from_user.username if message.from_user else None
        user_language = await asyncio.to_thread(
            self.db.get_user_language,
            chat_id,
        )

        if user_language is None:
            await asyncio.to_thread(
                self.db.add_user,
                chat_id,
                username,
                Config.DEFAULT_LANGUAGE,
            )
            await self.ask_for_language(chat_id)
        else:
            welcome_msg = self.translation.get("welcome", user_language)
            await self.bot.send_message(
                chat_id,
                welcome_msg,
                parse_mode="Markdown",
            )

    async def ask_for_language(self, chat_id: int):
        languages = self.translation.get_all_languages()
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=lang_name,
                        callback_data=f"set_lang_{lang_code}",
                    )
                ]
                for lang_code, lang_name in languages.items()
            ]
        )

        ask_msg = self.translation.get("choose_language", "en")
        await self.bot.send_message(
            chat_id,
            ask_msg,
            parse_mode="Markdown",
            reply_markup=keyboard,
        )

    async def handle_callback_query(self, call: CallbackQuery):
        if not call.message or not call.data:
            await call.answer()
            return

        if not call.data.startswith("set_lang_"):
            await call.answer()
            return

        chat_id = call.message.chat.id
        if not self.check_admin(call.from_user.id):
            await call.answer()
            return

        language = call.data.removeprefix("set_lang_")
        languages = self.translation.get_all_languages()

        if language not in languages:
            await call.answer()
            return

        await asyncio.to_thread(
            self.db.update_user_language,
            chat_id,
            language,
        )

        lang_name = languages.get(language, language)
        confirm_msg = self.translation.get(
            "language_set",
            language,
            language_name=lang_name,
        )

        await call.answer()
        await call.message.edit_text(
            confirm_msg,
            parse_mode="Markdown",
        )

        await asyncio.sleep(1)

        welcome_msg = self.translation.get("welcome", language)
        await self.bot.send_message(
            chat_id,
            welcome_msg,
            parse_mode="Markdown",
        )

    async def handle_help(self, message: Message):
        chat_id = message.chat.id
        if not self.check_admin(message.from_user.id if message.from_user else None):
            return

        language = await self.get_user_language(chat_id)
        help_text = self.translation.get("help", language)

        await self.bot.send_message(
            chat_id,
            help_text,
            parse_mode="Markdown",
        )

    async def handle_language(self, message: Message):
        chat_id = message.chat.id
        if not self.check_admin(message.from_user.id if message.from_user else None):
            return

        await self.ask_for_language(chat_id)
