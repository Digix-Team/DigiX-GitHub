import logging
import time
from datetime import datetime, timedelta
from threading import Thread
from typing import Dict, List
import telebot

from database import Database
from github_api import GitHubAPI
from config import Config
from translation_manager import TranslationManager

logger = logging.getLogger(__name__)


class MonitorManager:
    def __init__(self, db: Database, github_api: GitHubAPI, bot: telebot.TeleBot):
        self.db = db
        self.github = github_api
        self.bot = bot
        self.running = True
        self.translation = TranslationManager()
    
    def check_all_repositories(self):
        try:
            repos = self.db.get_all_monitored_repos()
            logger.info(f"Checking {len(repos)} repositories...")
            
            for repo in repos:
                self.check_repository(repo['repo_full_name'], repo['branch'])
                
        except Exception as e:
            logger.error(f"Error in check_all_repositories: {e}")
    
    def check_repository(self, repo_full_name: str, branch: str = 'main'):
        try:
            logger.info(f"Checking repository: {repo_full_name}")
            
            last_commit_date = self.db.get_last_commit_date(repo_full_name)
            
            if not last_commit_date:
                last_commit_date = datetime.now() - timedelta(hours=24)
                logger.info(f"First check for {repo_full_name}, checking last 24 hours")
            
            commits = self.github.get_latest_commits(repo_full_name, branch, last_commit_date)
            
            if not commits:
                logger.info(f"No new commits found for {repo_full_name}")
                return
                
            new_commits = []
            for commit in commits:
                if not self.db.is_commit_logged(repo_full_name, commit['sha']):
                    new_commits.append(commit)
                    
            if new_commits:
                logger.info(f"Found {len(new_commits)} new commits in {repo_full_name}")
                self.process_new_commits(repo_full_name, new_commits)
            else:
                logger.info(f"No new commits to process for {repo_full_name}")
                
        except Exception as e:
            logger.error(f"Error checking repository {repo_full_name}: {e}")
    
    def process_new_commits(self, repo_full_name: str, commits: List[Dict]):
        commits.sort(key=lambda x: x['date'], reverse=True)
        
        for commit in commits:
            self.db.log_commit(commit)
            
        if commits:
            latest_commit = commits[0]
            self.db.update_last_commit(repo_full_name, latest_commit['sha'], latest_commit['date'])
            
            subscribers = self.db.get_repo_subscribers(repo_full_name)
            logger.info(f"Sending notifications to {len(subscribers)} subscribers for {repo_full_name}")
            
            for chat_id in subscribers:
                try:
                    language = self.db.get_user_language(chat_id)
                    self.send_commit_notification(chat_id, repo_full_name, commits, language)
                except Exception as e:
                    logger.error(f"Failed to send notification to {chat_id}: {e}")
    
    def send_commit_notification(self, chat_id: int, repo_full_name: str, commits: List[Dict], language: str):
        if not commits:
            return
        
        for commit in commits[:5]:
            try:
                message = self._format_commit_message(repo_full_name, commit, language)
                self.bot.send_message(
                    chat_id, 
                    message, 
                    parse_mode='Markdown', 
                    disable_web_page_preview=True
                )
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"Error sending commit {commit['sha']} to {chat_id}: {e}")
        
        if len(commits) > 5:
            summary_msg = self.translation.get(
                'commit_summary', 
                language,
                repo_full_name=repo_full_name,
                total_commits=len(commits),
                extra_count=len(commits) - 5
            )
            
            try:
                self.bot.send_message(chat_id, summary_msg, parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Error sending summary to {chat_id}: {e}")
    
    def _format_commit_message(self, repo_full_name: str, commit: Dict, language: str) -> str:
        commit_time = commit['date'].strftime('%Y/%m/%d - %H:%M:%S')
        short_hash = commit['sha'][:7]
        
        commit_message = commit['message']
        if len(commit_message) > 300:
            commit_message = commit_message[:297] + "..."
        
        message = self.translation.get(
            'commit_message',
            language,
            repo_full_name=repo_full_name,
            commit_message=commit_message,
            author_name=commit['author_name'],
            commit_time=commit_time,
            short_hash=short_hash
        )
        
        changes_text = ""
        if commit.get('added', 0) > 0:
            if language == 'fa':
                changes_text += f"➕ {commit['added']} فایل جدید\n"
            else:
                changes_text += f"➕ {commit['added']} new files\n"
        
        if commit.get('removed', 0) > 0:
            if language == 'fa':
                changes_text += f"➖ {commit['removed']} فایل حذف شده\n"
            else:
                changes_text += f"➖ {commit['removed']} files removed\n"
        
        if commit.get('modified', 0) > 0:
            if language == 'fa':
                changes_text += f"✏️ {commit['modified']} فایل تغییر یافته\n"
            else:
                changes_text += f"✏️ {commit['modified']} files modified\n"
        
        if changes_text:
            if language == 'fa':
                message += f"📊 *تغییرات:*\n{changes_text}\n"
            else:
                message += f"📊 *Changes:*\n{changes_text}\n"
        
        if language == 'fa':
            message += f"""🔗 *لینک‌ها:*
• [مشاهده کامیت در GitHub]({commit['url']})
• [مشاهده ریپازیتوری](https://github.com/{repo_full_name})"""
        else:
            message += f"""🔗 *Links:*
• [View commit on GitHub]({commit['url']})
• [View repository](https://github.com/{repo_full_name})"""
        
        return message
    
    def start_monitoring(self):
        def monitoring_loop():
            logger.info("Monitoring loop started")
            while self.running:
                try:
                    self.check_all_repositories()
                except Exception as e:
                    logger.error(f"Monitoring loop error: {e}")
                
                time.sleep(Config.CHECK_INTERVAL)
        
        monitor_thread = Thread(target=monitoring_loop, daemon=True)
        monitor_thread.start()
        logger.info(f"✅ Monitoring started with interval {Config.CHECK_INTERVAL} seconds")
    
    def stop_monitoring(self):
        self.running = False
        logger.info("Monitoring stopped")