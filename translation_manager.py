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
                    'welcome': 'Welcome',
                    'help': 'Help',
                    'choose_language': 'Please choose your language:',
                    'language_set': 'Language has been set to {language_name}',
                    'repo_added': 'Repository successfully added: {repo_name}',
                    'repo_not_found': 'Repository not found: {repo_name}',
                    'repo_removed': 'Repository removed: {repo_name}',
                    'no_repositories': 'No repositories found',
                    'list_repos': 'Your repositories:',
                    'checking_repos': 'Checking {count} repositories...',
                    'check_complete': 'Check complete',
                    'stats': 'Statistics',
                    'connection_ok': 'Connection OK',
                    'connection_error': 'Connection error',
                    'unknown_command': 'Unknown command',
                    'commit_message': 'New commit: {commit_hash}',
                    'commit_summary': 'Commit summary: {total} commits'
                },
                'fa': {
                    'welcome': 'خوش آمدید',
                    'help': 'راهنما',
                    'choose_language': 'لطفاً زبان خود را انتخاب کنید:',
                    'language_set': 'زبان به {language_name} تنظیم شد',
                    'repo_added': 'ریپازیتوری با موفقیت اضافه شد: {repo_name}',
                    'repo_not_found': 'ریپازیتوری پیدا نشد: {repo_name}',
                    'repo_removed': 'ریپازیتوری حذف شد: {repo_name}',
                    'no_repositories': 'هیچ ریپازیتوری یافت نشد',
                    'list_repos': 'ریپازیتوری‌های شما:',
                    'checking_repos': 'در حال بررسی {count} ریپازیتوری...',
                    'check_complete': 'بررسی کامل شد',
                    'stats': 'آمار',
                    'connection_ok': 'اتصال موفق',
                    'connection_error': 'خطای اتصال',
                    'unknown_command': 'دستور ناشناخته',
                    'commit_message': 'کامیت جدید: {commit_hash}',
                    'commit_summary': 'خلاصه کامیت‌ها: {total} کامیت'
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