import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram.types import Message

from app.core.config import Config
from app.handlers.common import CommonHandlers


class RepositoryHandlers(CommonHandlers):
    def __init__(self, bot, db, github, translation):
        super().__init__(db)
        self.bot = bot
        self.github = github
        self.translation = translation

    async def handle_add(self, message: Message):
        chat_id = message.chat.id

        if not self.check_admin(message.from_user.id if message.from_user else None):
            return

        language = await self.get_user_language(chat_id)
        args = (message.text or "").split()

        if len(args) < 2:
            await message.answer(
                self.translation.get(
                    "repo_not_found",
                    language,
                    repo_full_name="[repository-name]",
                ),
                parse_mode="Markdown",
            )
            return

        repo_full_name = args[1].strip()

        if repo_full_name.count("/") != 1:
            await message.answer(
                self.translation.get("invalid_format", language),
                parse_mode="Markdown",
            )
            return

        owner, repo_name = repo_full_name.split("/", 1)
        if not owner or not repo_name:
            await message.answer(
                self.translation.get("invalid_format", language),
                parse_mode="Markdown",
            )
            return

        wait_msg = await self.bot.send_message(
            chat_id,
            self.translation.get(
                "checking_repo",
                language,
                repo_full_name=repo_full_name,
            ),
            parse_mode="Markdown",
        )

        try:
            repo_info = await asyncio.to_thread(
                self.github.get_repo_info,
                repo_full_name,
            )

            if not repo_info:
                await self.bot.edit_message_text(
                    self.translation.get(
                        "repo_not_found",
                        language,
                        repo_full_name=repo_full_name,
                    ),
                    chat_id=chat_id,
                    message_id=wait_msg.message_id,
                    parse_mode="Markdown",
                )
                return

            default_branch = repo_info.get("default_branch", "main")
            repo_url = repo_info["html_url"]

            await asyncio.to_thread(
                self.db.add_repository,
                chat_id,
                repo_full_name,
                repo_url,
                default_branch,
            )

            commits = await asyncio.to_thread(
                self.github.get_latest_commits,
                repo_full_name,
                default_branch,
            )

            if commits:
                latest_commit = commits[0]
                await asyncio.to_thread(
                    self.db.update_last_commit,
                    repo_full_name,
                    latest_commit["sha"],
                    latest_commit["date"],
                )
                await asyncio.to_thread(self.db.log_commit, latest_commit)

            success_msg = self.translation.get(
                "repo_added",
                language,
                repo_full_name=repo_full_name,
                default_branch=default_branch,
                repo_url=repo_url,
                check_interval=Config.CHECK_INTERVAL,
            )

            await self.bot.edit_message_text(
                success_msg,
                chat_id=chat_id,
                message_id=wait_msg.message_id,
                parse_mode="Markdown",
            )
        except Exception:
            await self.bot.edit_message_text(
                self.translation.get("connection_error", language),
                chat_id=chat_id,
                message_id=wait_msg.message_id,
                parse_mode="Markdown",
            )
            raise

    async def handle_remove(self, message: Message):
        chat_id = message.chat.id

        if not self.check_admin(message.from_user.id if message.from_user else None):
            return

        language = await self.get_user_language(chat_id)
        args = (message.text or "").split()

        if len(args) < 2:
            await message.answer(
                self.translation.get("remove_usage", language),
                parse_mode="Markdown",
            )
            return

        repo_full_name = args[1].strip()

        if repo_full_name.count("/") != 1:
            await message.answer(
                self.translation.get("invalid_format", language),
                parse_mode="Markdown",
            )
            return

        owner, repo_name = repo_full_name.split("/", 1)
        if not owner or not repo_name:
            await message.answer(
                self.translation.get("invalid_format", language),
                parse_mode="Markdown",
            )
            return

        await asyncio.to_thread(
            self.db.remove_repository,
            chat_id,
            repo_full_name,
        )

        await message.answer(
            self.translation.get(
                "repo_removed",
                language,
                repo_full_name=repo_full_name,
            ),
            parse_mode="Markdown",
        )

    async def handle_list(self, message: Message):
        chat_id = message.chat.id

        if not self.check_admin(message.from_user.id if message.from_user else None):
            return

        language = await self.get_user_language(chat_id)
        repos = await asyncio.to_thread(self.db.get_user_repos, chat_id)

        if not repos:
            await message.answer(
                self.translation.get("no_repositories", language),
                parse_mode="Markdown",
            )
            return

        list_text = self.translation.get("list_repos", language)

        for index, repo in enumerate(repos, 1):
            last_check = repo.get("last_check", "Unknown")

            if last_check:
                try:
                    if isinstance(last_check, datetime):
                        check_dt = last_check
                    else:
                        check_dt = datetime.fromisoformat(str(last_check))

                    if check_dt.tzinfo is None:
                        check_dt = check_dt.astimezone()

                    last_check = check_dt.astimezone(
                        ZoneInfo("Asia/Tehran")
                    ).strftime("%H:%M")
                except (ValueError, TypeError, OverflowError):
                    last_check = "Unknown"

            list_text += f"{index}. *{repo['repo_full_name']}*\n"
            list_text += (
                f"   🌿 {self.translation.get('branch_label', language)}: "
                f"{repo.get('branch', 'main')}\n"
            )
            list_text += (
                f"   🕐 {self.translation.get('last_check_label', language)}: "
                f"{last_check}\n"
            )
            list_text += f"   🔗 [View on GitHub]({repo['repo_url']})\n\n"

        await self.bot.send_message(
            chat_id,
            list_text,
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )
