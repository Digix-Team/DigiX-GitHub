from telebot.types import Message

from app.core.config import Config
from app.handlers.common import CommonHandlers


class MonitoringHandlers(CommonHandlers):
    def __init__(self, bot, db, github, monitor, translation):
        super().__init__(db)
        self.bot = bot
        self.github = github
        self.monitor = monitor
        self.translation = translation

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
        
        if self.github.test_connection():
            connection_status = self.translation.get('connected_status', language)
        else:
            connection_status = self.translation.get('disconnected_status', language)
        
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
            stats_text += self.translation.get('recent_repos_title', language) + "\n"

            for i, repo in enumerate(repos[:5], 1):
                stats_text += f"{i}. *{repo['repo_full_name']}*\n"
        
        stats_text += self.translation.get('stats_footer', language)

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
    
