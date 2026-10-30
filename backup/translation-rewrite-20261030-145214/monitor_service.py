import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from zoneinfo import ZoneInfo

from app.core.config import Config
from app.database.repository import Database
from app.integrations.github_api import GitHubAPI
from app.services.translation_service import TranslationManager

logger = logging.getLogger(__name__)


class MonitorManager:
    def __init__(
        self,
        db: Database,
        github_api: GitHubAPI,
        bot,
        translation: TranslationManager = None,
    ):
        self.db = db
        self.github = github_api
        self.bot = bot
        self.translation = translation or TranslationManager()
        self.running = False
        self._monitor_task = None
        self._check_lock = asyncio.Lock()

    async def check_all_repositories(self):
        async with self._check_lock:
            try:
                repos = await asyncio.to_thread(
                    self.db.get_all_monitored_repos
                )
                logger.info("Checking %s repositories...", len(repos))

                for repo in repos:
                    try:
                        await self.check_repository(
                            repo["repo_full_name"],
                            repo.get("branch", "main"),
                        )
                    except Exception:
                        logger.exception(
                            "Failed to check repository %s",
                            repo.get("repo_full_name", "unknown"),
                        )

            except Exception:
                logger.exception("Error in check_all_repositories")

    async def check_repository(
        self,
        repo_full_name: str,
        branch: str = "main",
    ):
        try:
            notifications = await asyncio.to_thread(
                self._collect_new_commits,
                repo_full_name,
                branch,
            )

            for chat_id, commits, language in notifications:
                await self.send_commit_notification(
                    chat_id,
                    repo_full_name,
                    commits,
                    language,
                )

        except Exception:
            logger.exception(
                "Error checking repository %s",
                repo_full_name,
            )
            raise

    def _collect_new_commits(self, repo_full_name: str, branch: str):
        logger.info("Checking repository: %s", repo_full_name)

        last_commit_date = self.db.get_last_commit_date(repo_full_name)

        if not last_commit_date:
            last_commit_date = datetime.now(timezone.utc) - timedelta(hours=24)
            logger.info(
                "First check for %s, checking last 24 hours",
                repo_full_name,
            )

        commits = self.github.get_latest_commits(
            repo_full_name,
            branch,
            last_commit_date,
        )

        if not commits:
            logger.info("No new commits found for %s", repo_full_name)
            return []

        new_commits = [
            commit
            for commit in commits
            if not self.db.is_commit_logged(
                repo_full_name,
                commit["sha"],
            )
        ]

        if not new_commits:
            logger.info("No new commits to process for %s", repo_full_name)
            return []

        new_commits.sort(key=lambda item: item["date"], reverse=True)
        logger.info(
            "Found %s new commits in %s",
            len(new_commits),
            repo_full_name,
        )

        for commit in new_commits:
            self.db.log_commit(commit)

        latest_commit = new_commits[0]
        self.db.update_last_commit(
            repo_full_name,
            latest_commit["sha"],
            latest_commit["date"],
        )

        subscribers = self.db.get_repo_subscribers(repo_full_name)
        logger.info(
            "Sending notifications to %s subscribers for %s",
            len(subscribers),
            repo_full_name,
        )

        notifications = []
        for chat_id in subscribers:
            try:
                language = self.db.get_user_language(chat_id) or Config.DEFAULT_LANGUAGE
                notifications.append((chat_id, new_commits, language))
            except Exception:
                logger.exception(
                    "Failed to prepare notification for %s",
                    chat_id,
                )

        return notifications

    async def send_commit_notification(
        self,
        chat_id: int,
        repo_full_name: str,
        commits: List[Dict],
        language: str,
    ):
        if not commits:
            return

        for commit in commits[:5]:
            try:
                message = self._format_commit_message(
                    repo_full_name,
                    commit,
                    language,
                )
                await self.bot.send_message(
                    chat_id,
                    message,
                    parse_mode="Markdown",
                    disable_web_page_preview=True,
                )
                await asyncio.sleep(0.5)

            except Exception:
                logger.exception(
                    "Error sending commit %s to %s",
                    commit.get("sha", "unknown"),
                    chat_id,
                )

        if len(commits) > 5:
            summary_msg = self.translation.get(
                "commit_summary",
                language,
                repo_name=repo_full_name,
                total=len(commits),
                repo_url=f"https://github.com/{repo_full_name}",
            )

            try:
                await self.bot.send_message(
                    chat_id,
                    summary_msg,
                    parse_mode="Markdown",
                )
            except Exception:
                logger.exception(
                    "Error sending commit summary to %s",
                    chat_id,
                )

    def _format_commit_message(
        self,
        repo_full_name: str,
        commit: Dict,
        language: str,
    ) -> str:
        commit_date = commit["date"]
        if commit_date.tzinfo is None:
            commit_date = commit_date.replace(tzinfo=timezone.utc)

        commit_time = commit_date.astimezone(
            ZoneInfo("Asia/Tehran")
        ).strftime("%Y/%m/%d - %H:%M:%S")

        short_hash = commit["sha"][:7]
        commit_message = commit["message"]

        if len(commit_message) > 300:
            commit_message = commit_message[:297] + "..."

        if language == "fa":
            message = "🚀 *کامیت جدید*\n\n"
            message += f"📁 *ریپازیتوری:* *{repo_full_name}*\n"
            message += f"📝 *پیام:* {commit_message}\n\n"
            message += f"👤 *نویسنده:* {commit['author_name']}\n"
            message += f"🕐 *زمان:* {commit_time}\n"
            message += f"🔑 *هش:* *{short_hash}*\n"
        else:
            message = "🚀 *New Commit*\n\n"
            message += f"📁 *Repository:* *{repo_full_name}*\n"
            message += f"📝 *Message:* {commit_message}\n\n"
            message += f"👤 *Author:* {commit['author_name']}\n"
            message += f"🕐 *Time:* {commit_time}\n"
            message += f"🔑 *Hash:* *{short_hash}*\n"

        changes_text = ""

        if commit.get("added", 0) > 0:
            if language == "fa":
                changes_text += f"➕ {commit['added']} فایل جدید\n"
            else:
                changes_text += f"➕ {commit['added']} new files\n"

        if commit.get("removed", 0) > 0:
            if language == "fa":
                changes_text += f"➖ {commit['removed']} فایل حذف شده\n"
            else:
                changes_text += f"➖ {commit['removed']} files removed\n"

        if commit.get("modified", 0) > 0:
            if language == "fa":
                changes_text += f"✏️ {commit['modified']} فایل تغییر یافته\n"
            else:
                changes_text += f"✏️ {commit['modified']} files modified\n"

        if changes_text:
            if language == "fa":
                message += f"\n📊 *تغییرات:*\n{changes_text}"
            else:
                message += f"\n📊 *Changes:*\n{changes_text}"

        if language == "fa":
            message += "\n🔗 *لینک‌ها:*\n"
            message += f"• [مشاهده کامیت در GitHub]({commit['url']})\n"
            message += (
                f"• [مشاهده ریپازیتوری]"
                f"(https://github.com/{repo_full_name})"
            )
        else:
            message += "\n🔗 *Links:*\n"
            message += f"• [View commit on GitHub]({commit['url']})\n"
            message += (
                f"• [View repository]"
                f"(https://github.com/{repo_full_name})"
            )

        return message

    async def start_monitoring(self):
        if self._monitor_task and not self._monitor_task.done():
            return

        self.running = True
        self._monitor_task = asyncio.create_task(
            self._monitoring_loop(),
            name="github-repository-monitor",
        )
        logger.info(
            "Monitoring started with interval %s seconds",
            Config.CHECK_INTERVAL,
        )

    async def _monitoring_loop(self):
        logger.info("Monitoring loop started")

        while self.running:
            await self.check_all_repositories()

            try:
                await asyncio.sleep(Config.CHECK_INTERVAL)
            except asyncio.CancelledError:
                break

    async def stop_monitoring(self):
        self.running = False

        task = self._monitor_task
        self._monitor_task = None

        if task and task is not asyncio.current_task():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        logger.info("Monitoring stopped")
