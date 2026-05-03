import json
import os
from typing import Dict, Any, Optional


class TranslationManager:
    def __init__(self, translation_file: str = 'translations.json'):
        self.translation_file = translation_file
        self.translations = self._load_translations()
    
    def _load_translations(self) -> Dict:
        """Load translations from JSON file"""
        if not os.path.exists(self.translation_file):
            default_translations = {
                'en': {
                    'welcome': '🤖 *GitHub Commit Monitor Bot*\n\nThis bot monitors your private/public GitHub repositories for changes.\n\n*Main Commands:*\n📋 /list - My repositories\n➕ /add - Add new repository\n➖ /remove - Remove repository\n🔍 /check - Manual check\n📊 /stats - Bot statistics\n🌐 /language - Change language\n❓ /help - Complete guide',
                    'help': '📚 *Help Guide*\n\n'
                           'Available commands:\n'
                           '/start - Start the bot\n'
                           '/help - Show this help\n'
                           '/language - Change language\n'
                           '/add - Add a repository to monitor\n'
                           '/remove - Remove a repository from monitoring\n'
                           '/list - List all monitored repositories\n'
                           '/check - Manually check all repositories\n'
                           '/stats - View bot statistics\n'
                           '/status - Check GitHub API connection status\n\n'
                           '*How to add a repository:*\n'
                           '_/add username/repository-name_\n\n'
                           '*Example:* _/add facebook/react_',
                    'choose_language': '🌐 Please choose your language:',
                    'language_set': '✅ Language has been set to {language_name}',
                    'repo_added': '✅ *Repository successfully added!*\n\n'
                                 '📦 *Name:* {repo_full_name}\n'
                                 '🌿 *Branch:* {default_branch}\n'
                                 '🔗 *Link:* [View on GitHub]({repo_url})\n'
                                 '⏱️ *Check interval:* Every {check_interval} seconds\n\n'
                                 '🔔 You will be notified of new commits.',
                    'repo_not_found': '❌ Repository *{repo_full_name}* not found!\n\n'
                                    'Please check the name and try again.\n'
                                    '*Correct format:* _username/repository-name_',
                    'repo_removed': '🗑️ Repository *{repo_full_name}* has been removed from monitoring.',
                    'no_repositories': '📭 No repositories are being monitored.\n\n'
                                      'Use _/add username/repository-name_ to add one.',
                    'list_repos': '📋 *Your monitored repositories:*\n\n',
                    'checking_repos': '🔄 Checking {count} repository(ies) for new commits...',
                    'check_complete': '✅ Manual check completed!',
                    'stats': '📊 *Bot Statistics*\n\n'
                           '📁 *Your repositories:* {user_repos}\n'
                           '🌍 *Total monitored repos:* {total_repos}\n'
                           '⏱️ *Check interval:* {interval} seconds\n'
                           '🔌 *GitHub API:* {connection_status}',
                    'connection_ok': '✅ *GitHub API Status:* Connected\n\n'
                                   'Bot is functioning normally.',
                    'connection_error': '❌ *GitHub API Status:* Disconnected\n\n'
                                      'Please check your GitHub token.',
                    'unknown_command': '❓ Unknown command.\n\n'
                                      'Use _/help_ to see available commands.',
                    'commit_message': '📝 *New Commit Detected!*\n\n'
                                    '📦 *Repository:* [{repo_name}]({repo_url})\n'
                                    '🔑 *Commit Hash:* _{commit_hash}_\n'
                                    '👤 *Author:* {author}\n'
                                    '💬 *Message:* {message}\n'
                                    '🔗 [View Commit]({commit_url})',
                    'commit_summary': '📊 *Commit Summary*\n\n'
                                    '📦 *Repository:* {repo_name}\n'
                                    '🆕 *New commits found:* {total}\n'
                                    '🔗 [View Repository]({repo_url})',
                    'invalid_format': '❌ *Invalid format!*\n\n'
                                     'Please use:\n'
                                     '_/add username/repository-name_\n\n'
                                     '*Example:* _/add facebook/react_',
                    'checking_repo': '🔍 Checking repository *{repo_full_name}*...',
                    'remove_usage': '⚠️ *Usage:* _/remove username/repository-name_\n\n'
                                   '*Example:* _/remove facebook/react_',
                    'connected_status': '✅ Connected',
                    'disconnected_status': '❌ Disconnected',
                    'recent_repos_title': '*Your Recent Repositories:*',
                    'stats_footer': '\n📈 Use _/add_ to add a new repository.',
                    'branch_label': 'Branch',
                    'last_check_label': 'Last check'
                },
                'fa': {
                    'welcome': '🤖 *ربات مانیتورینگ کامیت‌های GitHub*\n\nاین ربات تغییرات ریپازیتوری‌های خصوصی/عمومی GitHub شما را مانیتور می‌کند.\n\n*دستورات اصلی:*\n📋 /list - مشاهده ریپازیتوری‌های من\n➕ /add - افزودن ریپازیتوری جدید\n➖ /remove - حذف ریپازیتوری\n🔍 /check - چک کردن دستی\n📊 /stats - آمار ربات\n🌐 /language - تغییر زبان\n❓ /help - راهنمای کامل',
                    'help': '📚 *راهنما*\n\n'
                           'دستورات موجود:\n'
                           '/start - شروع ربات\n'
                           '/help - نمایش این راهنما\n'
                           '/language - تغییر زبان\n'
                           '/add - افزودن ریپازیتوری برای مانیتور\n'
                           '/remove - حذف ریپازیتوری از مانیتور\n'
                           '/list - لیست ریپازیتوری‌های تحت نظر\n'
                           '/check - بررسی دستی همه ریپازیتوری‌ها\n'
                           '/stats - مشاهده آمار ربات\n'
                           '/status - وضعیت اتصال به GitHub API\n\n'
                           '*نحوه افزودن ریپازیتوری:*\n'
                           '_/add username/repository-name_\n\n'
                           '*مثال:* _/add facebook/react_',
                    'choose_language': '🌐 لطفاً زبان خود را انتخاب کنید:',
                    'language_set': '✅ زبان به {language_name} تنظیم شد',
                    'repo_added': '✅ *ریپازیتوری با موفقیت اضافه شد!*\n\n'
                                 '📦 *نام:* {repo_full_name}\n'
                                 '🌿 *شاخه:* {default_branch}\n'
                                 '🔗 *لینک:* [مشاهده در گیت‌هاب]({repo_url})\n'
                                 '⏱️ *فاصله بررسی:* هر {check_interval} ثانیه\n\n'
                                 '🔔 از کامیت‌های جدید مطلع خواهید شد.',
                    'repo_not_found': '❌ ریپازیتوری *{repo_full_name}* پیدا نشد!\n\n'
                                    'لطفاً نام را بررسی کنید و دوباره تلاش کنید.\n'
                                    '*قالب صحیح:* _username/repository-name_',
                    'repo_removed': '🗑️ ریپازیتوری *{repo_full_name}* از لیست نظارت حذف شد.',
                    'no_repositories': '📭 هیچ ریپازیتوری در حال نظارت نیست.\n\n'
                                      'برای افزودن از _/add username/repository-name_ استفاده کنید.',
                    'list_repos': '📋 *ریپازیتوری‌های تحت نظر شما:*\n\n',
                    'checking_repos': '🔄 در حال بررسی {count} ریپازیتوری برای کامیت‌های جدید...',
                    'check_complete': '✅ بررسی دستی کامل شد!',
                    'stats': '📊 *آمار ربات*\n\n'
                           '📁 *ریپازیتوری‌های شما:* {user_repos}\n'
                           '🌍 *کل ریپازیتوری‌های تحت نظر:* {total_repos}\n'
                           '⏱️ *فاصله بررسی:* {interval} ثانیه\n'
                           '🔌 *وضعیت GitHub API:* {connection_status}',
                    'connection_ok': '✅ *وضعیت GitHub API:* متصل\n\n'
                                   'ربات به درستی کار می‌کند.',
                    'connection_error': '❌ *وضعیت GitHub API:* قطع\n\n'
                                      'لطفاً توکن گیت‌هاب خود را بررسی کنید.',
                    'unknown_command': '❓ دستور ناشناخته.\n\n'
                                      'برای مشاهده دستورات موجود از _/help_ استفاده کنید.',
                    'commit_message': '📝 *کامیت جدید تشخیص داده شد!*\n\n'
                                    '📦 *ریپازیتوری:* [{repo_name}]({repo_url})\n'
                                    '🔑 *هش کامیت:* _{commit_hash}_\n'
                                    '👤 *نویسنده:* {author}\n'
                                    '💬 *پیام:* {message}\n'
                                    '🔗 [مشاهده کامیت]({commit_url})',
                    'commit_summary': '📊 *خلاصه کامیت‌ها*\n\n'
                                    '📦 *ریپازیتوری:* {repo_name}\n'
                                    '🆕 *کامیت‌های جدید یافت شد:* {total}\n'
                                    '🔗 [مشاهده ریپازیتوری]({repo_url})',
                    'invalid_format': '❌ *قالب نامعتبر!*\n\n'
                                     'لطفاً از قالب زیر استفاده کنید:\n'
                                     '_/add username/repository-name_\n\n'
                                     '*مثال:* _/add facebook/react_',
                    'checking_repo': '🔍 در حال بررسی ریپازیتوری *{repo_full_name}*...',
                    'remove_usage': '⚠️ *طریقه استفاده:* _/remove username/repository-name_\n\n'
                                   '*مثال:* _/remove facebook/react_',
                    'connected_status': '✅ متصل',
                    'disconnected_status': '❌ قطع',
                    'recent_repos_title': ' *آخرین ریپازیتوری‌های شما:*',
                    'stats_footer': '\n📈 برای افزودن ریپازیتوری جدید از _/add_ استفاده کنید.',
                    'branch_label': 'شاخه',
                    'last_check_label': 'آخرین بررسی'
                }
            }
            with open(self.translation_file, 'w', encoding='utf-8') as f:
                json.dump(default_translations, f, ensure_ascii=False, indent=2)
            return default_translations
        
        try:
            with open(self.translation_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading translations: {e}")
            return {'en': {}, 'fa': {}}
    
    def get(self, key: str, language: str = 'en', **kwargs) -> str:
        """Get translation for a key with optional formatting"""
        try:
            translation = self.translations.get(language, {}).get(key, key)
            
            if translation == key and language != 'en':
                translation = self.translations.get('en', {}).get(key, key)
            
            if kwargs and isinstance(translation, str):
                try:
                    translation = translation.format(**kwargs)
                except (KeyError, ValueError) as format_error:
                    print(f"Formatting error for key '{key}': {format_error}")
                    pass
            
            return translation
        except Exception as e:
            print(f"Error getting translation for key '{key}', language '{language}': {e}")
            return key
    
    def get_all_languages(self) -> Dict[str, str]:
        """Get all available languages with display names"""
        return {
            'en': 'English 🇺🇸',
            'fa': 'فارسی 🇮🇷'
        }
    
    def reload_translations(self):
        """Reload translations from file"""
        self.translations = self._load_translations()