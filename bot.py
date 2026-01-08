import telebot
import logging
import threading
import time
import atexit
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

from config import Config
from database import Database
from github_api import GitHubAPI
from monitor import MonitorManager
from translation_manager import TranslationManager

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, Config.LOG_LEVEL),
    handlers=[
        logging.FileHandler(Config.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(Config.BOT_TOKEN)
db = Database()
github = GitHubAPI(Config.GITHUB_TOKEN)
translation = TranslationManager()
monitor = MonitorManager(db, github, bot)


class BotHandler:
    def __init__(self):
        self.bot = bot
        self.db = db
        self.github = github
        self.monitor = monitor
        self.translation = translation
        
        self.register_handlers()
    
    def register_handlers(self):
        @self.bot.message_handler(commands=['start'])
        def start_command(message: Message):
            self.handle_start(message)
        
        @self.bot.message_handler(commands=['help'])
        def help_command(message: Message):
            self.handle_help(message)
        
        @self.bot.message_handler(commands=['language'])
        def language_command(message: Message):
            self.handle_language(message)
        
        @self.bot.message_handler(commands=['add'])
        def add_command(message: Message):
            self.handle_add(message)
        
        @self.bot.message_handler(commands=['remove'])
        def remove_command(message: Message):
            self.handle_remove(message)
        
        @self.bot.message_handler(commands=['list'])
        def list_command(message: Message):
            self.handle_list(message)
        
        @self.bot.message_handler(commands=['check'])
        def check_command(message: Message):
            self.handle_check(message)
        
        @self.bot.message_handler(commands=['stats'])
        def stats_command(message: Message):
            self.handle_stats(message)
        
        @self.bot.message_handler(commands=['status'])
        def status_command(message: Message):
            self.handle_status(message)
        
        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_callback(call):
            self.handle_callback_query(call)
    
    def check_admin(self, chat_id: int) -> bool:
        return chat_id in Config.ADMIN_CHAT_ID
    
    def get_user_language(self, chat_id: int) -> str:
        language = self.db.get_user_language(chat_id)
        if language is None:
            self.db.add_user(chat_id, None, Config.DEFAULT_LANGUAGE)
            return Config.DEFAULT_LANGUAGE
        return language
    
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
    
    def handle_add(self, message: Message):
        chat_id = message.chat.id
        
        if not self.check_admin(chat_id):
            return
        
        language = self.get_user_language(chat_id)
        args = message.text.split()
        
        if len(args) < 2:
            self.bot.reply_to(
                message,
                self.translation.get('repo_not_found', language, repo_full_name="[repository-name]"),
                parse_mode='Markdown'
            )
            return
        
        repo_full_name = args[1].strip()
        
        if '/' not in repo_full_name or repo_full_name.count('/') != 1:
            self.bot.reply_to(
                message,
                "❌ Invalid format!\nCorrect format: username/repository-name",
                parse_mode='Markdown'
            )
            return
        
        wait_msg = self.bot.send_message(
            chat_id,
            f"🔍 Checking repository *{repo_full_name}*...",
            parse_mode='Markdown'
        )
        
        repo_info = self.github.get_repo_info(repo_full_name)
        
        if not repo_info:
            self.bot.edit_message_text(
                self.translation.get(
                    'repo_not_found',
                    language,
                    repo_full_name=repo_full_name
                ),
                chat_id,
                wait_msg.message_id,
                parse_mode='Markdown'
            )
            return
        
        default_branch = repo_info.get('default_branch', 'main')
        repo_url = repo_info['html_url']
        
        self.db.add_repository(chat_id, repo_full_name, repo_url, default_branch)
        
        commits = self.github.get_latest_commits(repo_full_name, default_branch)
        if commits:
            latest_commit = commits[0]
            self.db.update_last_commit(repo_full_name, latest_commit['sha'], latest_commit['date'])
            self.db.log_commit(latest_commit)
        
        success_msg = self.translation.get(
            'repo_added',
            language,
            repo_full_name=repo_full_name,
            default_branch=default_branch,
            repo_url=repo_url,
            check_interval=Config.CHECK_INTERVAL
        )
        
        self.bot.edit_message_text(
            success_msg,
            chat_id,
            wait_msg.message_id,
            parse_mode='Markdown'
        )
    
    def handle_remove(self, message: Message):
        chat_id = message.chat.id
        
        if not self.check_admin(chat_id):
            return
        
        language = self.get_user_language(chat_id)
        args = message.text.split()
        
        if len(args) < 2:
            self.bot.reply_to(
                message,
                f"⚠️ Please enter repository name:\n_/remove username/repository-name_",
                parse_mode='Markdown'
            )
            return
        
        repo_full_name = args[1].strip()
        
        self.db.remove_repository(chat_id, repo_full_name)
        
        confirm_msg = self.translation.get(
            'repo_removed',
            language,
            repo_full_name=repo_full_name
        )
        
        self.bot.reply_to(message, confirm_msg, parse_mode='Markdown')
    
    def handle_list(self, message: Message):
        chat_id = message.chat.id
        
        if not self.check_admin(chat_id):
            return
        
        language = self.get_user_language(chat_id)
        repos = self.db.get_user_repos(chat_id)
        
        if not repos:
            no_repos_msg = self.translation.get('no_repositories', language)
            self.bot.send_message(chat_id, no_repos_msg, parse_mode='Markdown')
            return
        
        list_text = self.translation.get('list_repos', language)
        
        for i, repo in enumerate(repos, 1):
            last_check = repo.get('last_check', 'Unknown')
            if last_check and not isinstance(last_check, str):
                try:
                    last_check = datetime.strptime(
                        str(last_check),
                        '%Y-%m-%d %H:%M:%S.%f' if '.' in str(last_check) else '%Y-%m-%d %H:%M:%S'
                    ).strftime('%H:%M')
                except:
                    last_check = 'Unknown'
            
            list_text += f"{i}. *{repo['repo_full_name']}*\n"
            list_text += f"   🌿 Branch: {repo.get('branch', 'main')}\n"
            list_text += f"   🕐 Last check: {last_check}\n"
            list_text += f"   🔗 [View on GitHub]({repo['repo_url']})\n\n"
        
        self.bot.send_message(
            chat_id,
            list_text,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
    
    def handle_check(self, message: Message):
        chat_id = message.chat.id
        
        if not self.check_admin(chat_id):
            return
        
        language = self.get_user_language(chat_id)
        repos = self.db.get_user_repos(chat_id)
        
        if not repos:
            no_repos_msg = self.translation.get('no_repositories', language)
            self.bot.send_message(chat_id, no_repos_msg, parse_mode='Markdown')
            return
        
        checking_msg = self.translation.get(
            'checking_repos',
            language,
            count=len(repos)
        )
        
        self.bot.send_message(chat_id, checking_msg, parse_mode='Markdown')
        
        for repo in repos:
            self.monitor.check_repository(
                repo['repo_full_name'],
                repo.get('branch', 'main')
            )
        
        complete_msg = self.translation.get('check_complete', language)
        self.bot.send_message(chat_id, complete_msg, parse_mode='Markdown')
    
    def handle_stats(self, message: Message):
        chat_id = message.chat.id
        
        if not self.check_admin(chat_id):
            return
        
        language = self.get_user_language(chat_id)
        
        user_repos = len(self.db.get_user_repos(chat_id))
        all_repos = len(self.db.get_all_monitored_repos())
        connection_status = '✅ Connected' if self.github.test_connection() else '❌ Disconnected'
        
        if language == 'fa':
            connection_status = '✅ متصل' if self.github.test_connection() else '❌ قطع'
        
        stats_text = self.translation.get(
            'stats',
            language,
            user_repos=user_repos,
            total_repos=all_repos,
            interval=Config.CHECK_INTERVAL,
            connection_status=connection_status
        )
        
        repos = self.db.get_user_repos(chat_id)
        if repos:
            if language == 'fa':
                stats_text += "*آخرین ریپازیتوری‌های شما:*\n"
            else:
                stats_text += "*Your Recent Repositories:*\n"
            
            for i, repo in enumerate(repos[:5], 1):
                stats_text += f"{i}. *{repo['repo_full_name']}*\n"
        
        if language == 'fa':
            stats_text += f"\n📈 از دستور */add* برای افزودن ریپازیتوری جدید استفاده کنید."
        else:
            stats_text += f"\n📈 Use */add* command to add new repository."
        
        self.bot.send_message(chat_id, stats_text, parse_mode='Markdown')
    
    def handle_status(self, message: Message):
        chat_id = message.chat.id
        
        if not self.check_admin(chat_id):
            return
        
        language = self.get_user_language(chat_id)
        
        if self.github.test_connection():
            status_msg = self.translation.get('connection_ok', language)
        else:
            status_msg = self.translation.get('connection_error', language)
        
        self.bot.send_message(chat_id, status_msg, parse_mode='Markdown')
    
    def handle_unknown(self, message: Message):
        chat_id = message.chat.id
        
        if not self.check_admin(chat_id):
            return
        
        language = self.get_user_language(chat_id)
        unknown_msg = self.translation.get('unknown_command', language)
        
        self.bot.reply_to(message, unknown_msg, parse_mode='Markdown')


def main():
    logger.info("=" * 50)
    logger.info("Starting GitHub Commit Monitor Bot")
    logger.info("=" * 50)
    
    logger.info("Testing GitHub API connection...")
    if not github.test_connection():
        logger.error("❌ GitHub API connection failed! Check your token.")
        return
    
    logger.info("✅ GitHub API connection successful")
    
    bot_handler = BotHandler()
    
    monitor.start_monitoring()
    logger.info(f"✅ Monitoring started with {Config.CHECK_INTERVAL} second interval")
    
    def shutdown_handler():
        monitor.stop_monitoring()
        logger.info("🛑 Bot is shutting down...")
    
    atexit.register(shutdown_handler)
    
    logger.info("🤖 Starting Telegram bot...")
    
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        logger.error(f"Bot polling error: {e}")


if __name__ == '__main__':
    main()