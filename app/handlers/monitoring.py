import asyncio

from aiogram.types import Message

from app.core.config import Config
from app.handlers.common import CommonHandlers


class MonitoringHandlers(CommonHandlers):
    def __init__(self, bot, db, github, monitor, translation):
        super().__init__(db)
        self.bot = bot
        self.github = github
        self.monitor = monitor
        self.translation = translation

    async def handle_check(self, message: Message):
        chat_id = message.chat.id
        if not self.check_admin(message.from_user.id if message.from_user else None):
            return

        language = await self.get_user_language(chat_id)
        repos = await asyncio.to_thread(self.db.get_user_repos, chat_id)

        if not repos:
            await self.bot.send_message(
                chat_id,
                self.translation.get("no_repositories", language),
                parse_mode="Markdown",
            )
            return

        await self.bot.send_message(
            chat_id,
            self.translation.get(
                "checking_repos",
                language,
                count=len(repos),
            ),
            parse_mode="Markdown",
        )

        failed_repositories = []

        for repo in repos:
            try:
                await self.monitor.check_repository(
                    repo["repo_full_name"],
                    repo.get("branch", "main"),
                )
            except Exception:
                failed_repositories.append(repo["repo_full_name"])

        complete_text = self.translation.get("check_complete", language)
        if failed_repositories:
            complete_text += "\\n\\nFailed repositories:\\n"
            complete_text += "\\n".join(
                f"- {name}" for name in failed_repositories
            )

        await self.bot.send_message(
            chat_id,
            complete_text,
            parse_mode="Markdown",
        )

    async def handle_stats(self, message: Message):
        chat_id = message.chat.id
        if not self.check_admin(message.from_user.id if message.from_user else None):
            return

        language = await self.get_user_language(chat_id)

        repos = await asyncio.to_thread(self.db.get_user_repos, chat_id)
        all_repos = await asyncio.to_thread(
            self.db.get_all_monitored_repos,
        )
        connected = await asyncio.to_thread(self.github.test_connection)

        if connected:
            connection_status = self.translation.get(
                "connected_status",
                language,
            )
        else:
            connection_status = self.translation.get(
                "disconnected_status",
                language,
            )

        stats_text = self.translation.get(
            "stats",
            language,
            user_repos=len(repos),
            total_repos=len(all_repos),
            interval=Config.CHECK_INTERVAL,
            connection_status=connection_status,
        )

        if repos:
            stats_text += self.translation.get(
                "recent_repos_title",
                language,
            ) + "\n"

            for index, repo in enumerate(repos[:5], 1):
                stats_text += f"{index}. *{repo['repo_full_name']}*\n"

        stats_text += self.translation.get("stats_footer", language)

        await self.bot.send_message(
            chat_id,
            stats_text,
            parse_mode="Markdown",
        )

    async def handle_status(self, message: Message):
        chat_id = message.chat.id
        if not self.check_admin(message.from_user.id if message.from_user else None):
            return

        language = await self.get_user_language(chat_id)
        connected = await asyncio.to_thread(self.github.test_connection)

        if connected:
            status_text = self.translation.get("connection_ok", language)
        else:
            status_text = self.translation.get("connection_error", language)

        await self.bot.send_message(
            chat_id,
            status_text,
            parse_mode="Markdown",
        )
