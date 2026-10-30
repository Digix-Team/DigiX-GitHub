from app.core.config import Config


class CommonHandlers:
    def __init__(self, db):
        self.db = db

    @staticmethod
    def check_admin(chat_id: int) -> bool:
        return chat_id in Config.ADMIN_CHAT_ID

    def get_user_language(self, chat_id: int) -> str:
        language = self.db.get_user_language(chat_id)
        if language is None:
            self.db.add_user(chat_id, None, Config.DEFAULT_LANGUAGE)
            return Config.DEFAULT_LANGUAGE
        return language
