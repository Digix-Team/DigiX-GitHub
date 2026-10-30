import asyncio

from app.core.config import Config


class CommonHandlers:
    def __init__(self, db):
        self.db = db

    @staticmethod
    def check_admin(user_id: int | None) -> bool:
        return user_id is not None and user_id in Config.ADMIN_CHAT_ID

    async def get_user_language(self, chat_id: int) -> str:
        language = await asyncio.to_thread(
            self.db.get_user_language,
            chat_id,
        )

        if language is None:
            await asyncio.to_thread(
                self.db.add_user,
                chat_id,
                None,
                Config.DEFAULT_LANGUAGE,
            )
            return Config.DEFAULT_LANGUAGE

        return language
