# config.py
import os
import re
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    if not BOT_TOKEN:
        raise ValueError("❌ BOT_TOKEN is not set in environment variables!")
    
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    if not GITHUB_TOKEN:
        raise ValueError("❌ GITHUB_TOKEN is not set in environment variables!")
    
    CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', 60))
    
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'github_bot.db')
    
    LOG_FILE = os.getenv('LOG_FILE', 'github_bot.log')
    
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    admin_ids_str = os.getenv('ADMIN_CHAT_IDS', '4575790772')
    
    try:
        # حذف براکت‌ها و فاصله‌ها
        admin_ids_str = admin_ids_str.strip()
        
        # حذف براکت شروع و پایان اگر وجود دارند
        if admin_ids_str.startswith('[') and admin_ids_str.endswith(']'):
            admin_ids_str = admin_ids_str[1:-1]
        
        if admin_ids_str:
            # split کردن با کاما و تبدیل به عدد
            ADMIN_CHAT_ID = [int(id.strip()) for id in admin_ids_str.split(',') if id.strip()]
        else:
            ADMIN_CHAT_ID = []
    except ValueError:
        raise ValueError("❌ ADMIN_CHAT_IDS must be comma-separated integers! Example: '123,456,789' or '[123,456,789]'")
    
    LANGUAGES = {
        'en': 'English',
        'fa': 'فارسی'
    }
    
    DEFAULT_LANGUAGE = 'en'
    
    @classmethod
    def validate_config(cls):
        """Validate configuration and log warnings for development mode"""
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Check if using default admin ID (for security warning)
        if cls.ADMIN_CHAT_ID == [4575790772]:
            logger.warning("⚠️  Using default ADMIN_CHAT_ID. Consider changing it in .env file!")
        
        # Validate tokens format (basic checks)
        if len(cls.BOT_TOKEN) < 10:
            logger.warning("⚠️  BOT_TOKEN seems too short!")
        
        if not cls.GITHUB_TOKEN.startswith('ghp_') and not cls.GITHUB_TOKEN.startswith('github_pat_'):
            logger.warning("⚠️  GITHUB_TOKEN format might be incorrect!")
        
        logger.info(f"✅ Config loaded: {len(cls.ADMIN_CHAT_ID)} admin(s), check interval: {cls.CHECK_INTERVAL}s")


if __name__ != "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    Config.validate_config()