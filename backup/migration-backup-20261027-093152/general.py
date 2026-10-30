import time
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from app.core.config import Config
from app.handlers.common import CommonHandlers


class GeneralHandlers(CommonHandlers):
    def __init__(self, bot, db, translation):
        super().__init__(db)
        self.bot = bot
        self.translation = translation

    def handle_start(self, message: Message):
        chat_id = message.chat.id
        
        if not self.check_admin(chat_id):
            return
        
        username = message.from_user.username
        
        user_language = self.db.get_user_language(chat_id)
        
        if user_language is None:
            self.db.add_user(chat_id, username, Config.DEFAULT_LANGUAGE)
            self.ask_for_language(chat_id)
        else:
            welcome_msg = self.translation.get('welcome', user_language)
            self.bot.send_message(chat_id, welcome_msg, parse_mode='Markdown')
    
    def ask_for_language(self, chat_id: int):
        keyboard = InlineKeyboardMarkup()
        
        languages = self.translation.get_all_languages()
        for lang_code, lang_name in languages.items():
            keyboard.add(
                InlineKeyboardButton(
                    lang_name,
                    callback_data=f"set_lang_{lang_code}"
                )
            )
        
        ask_msg = self.translation.get('choose_language', 'en')
        self.bot.send_message(
            chat_id,
            ask_msg,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    
    def handle_callback_query(self, call):
        chat_id = call.message.chat.id
        message_id = call.message.message_id
        
        if call.data.startswith('set_lang_'):
            language = call.data.split('_')[-1]
            
            self.db.update_user_language(chat_id, language)
            
            languages = self.translation.get_all_languages()
            lang_name = languages.get(language, language)
            
            confirm_msg = self.translation.get('language_set', language, language_name=lang_name)
            
            self.bot.edit_message_text(
                confirm_msg,
                chat_id,
                message_id,
                parse_mode='Markdown'
            )
            
            time.sleep(1)
            welcome_msg = self.translation.get('welcome', language)
            self.bot.send_message(chat_id, welcome_msg, parse_mode='Markdown')
    
    def handle_help(self, message: Message):
        chat_id = message.chat.id
        
        if not self.check_admin(chat_id):
            return
        
        language = self.get_user_language(chat_id)
        help_text = self.translation.get('help', language)
        
        self.bot.send_message(chat_id, help_text, parse_mode='Markdown')
    
    def handle_language(self, message: Message):
        chat_id = message.chat.id
        
        if not self.check_admin(chat_id):
            return
        
        self.ask_for_language(chat_id)
