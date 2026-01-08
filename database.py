import sqlite3
import json
import os
from datetime import datetime
from threading import Lock
from typing import Dict, List, Optional
from config import Config


class Database:
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.db_path = Config.DATABASE_PATH
            self.lock = Lock()
            self.init_db()
            self._initialized = True
    
    def init_db(self):
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute('''CREATE TABLE IF NOT EXISTS users
                        (chat_id INTEGER PRIMARY KEY, 
                         username TEXT,
                         language TEXT DEFAULT 'en',
                         joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
            
            c.execute('''CREATE TABLE IF NOT EXISTS repositories
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         chat_id INTEGER,
                         repo_full_name TEXT,
                         repo_url TEXT,
                         last_commit_sha TEXT,
                         last_check TIMESTAMP,
                         last_commit_date TIMESTAMP,
                         branch TEXT DEFAULT 'main',
                         UNIQUE(chat_id, repo_full_name),
                         FOREIGN KEY (chat_id) REFERENCES users (chat_id))''')
            
            c.execute('''CREATE TABLE IF NOT EXISTS commit_history
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         repo_full_name TEXT,
                         commit_sha TEXT,
                         commit_message TEXT,
                         author_name TEXT,
                         author_email TEXT,
                         commit_date TIMESTAMP,
                         commit_url TEXT,
                         added INTEGER DEFAULT 0,
                         removed INTEGER DEFAULT 0,
                         modified INTEGER DEFAULT 0,
                         detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
            
            conn.commit()
            conn.close()
    
    def add_user(self, chat_id: int, username: str = None, language: str = 'en'):
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''INSERT OR IGNORE INTO users (chat_id, username, language) 
                        VALUES (?, ?, ?)''', (chat_id, username, language))
            conn.commit()
            conn.close()
    
    def get_user_language(self, chat_id: int) -> Optional[str]:
        """دریافت زبان کاربر - اگر کاربر وجود نداشت None برمی‌گرداند"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''SELECT language FROM users WHERE chat_id = ?''', (chat_id,))
            result = c.fetchone()
            conn.close()
            
            if result:
                return result[0]
            return None
    
    def update_user_language(self, chat_id: int, language: str):
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute('''SELECT 1 FROM users WHERE chat_id = ?''', (chat_id,))
            if not c.fetchone():
                c.execute('''INSERT INTO users (chat_id, language) VALUES (?, ?)''', 
                         (chat_id, language))
            else:
                c.execute('''UPDATE users SET language = ? WHERE chat_id = ?''', 
                         (language, chat_id))
            
            conn.commit()
            conn.close()
    
    def add_repository(self, chat_id: int, repo_full_name: str, repo_url: str, branch: str = 'main'):
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute('''SELECT 1 FROM users WHERE chat_id = ?''', (chat_id,))
            if not c.fetchone():
                c.execute('''INSERT OR IGNORE INTO users (chat_id, language) VALUES (?, ?)''', 
                         (chat_id, Config.DEFAULT_LANGUAGE))
            
            c.execute('''DELETE FROM repositories 
                        WHERE chat_id = ? AND repo_full_name = ?''', 
                     (chat_id, repo_full_name))
            
            c.execute('''INSERT INTO repositories 
                        (chat_id, repo_full_name, repo_url, branch, last_check)
                        VALUES (?, ?, ?, ?, ?)''',
                     (chat_id, repo_full_name, repo_url, branch, datetime.now()))
            
            conn.commit()
            conn.close()
    
    def remove_repository(self, chat_id: int, repo_full_name: str):
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''DELETE FROM repositories 
                        WHERE chat_id = ? AND repo_full_name = ?''',
                     (chat_id, repo_full_name))
            conn.commit()
            conn.close()
    
    def get_user_repos(self, chat_id: int) -> List[Dict]:
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute('''SELECT * FROM repositories 
                        WHERE chat_id = ? 
                        ORDER BY repo_full_name''', (chat_id,))
            rows = c.fetchall()
            conn.close()
            return [dict(row) for row in rows]
    
    def get_all_monitored_repos(self) -> List[Dict]:
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute('''SELECT DISTINCT repo_full_name, repo_url, branch 
                        FROM repositories''')
            rows = c.fetchall()
            conn.close()
            return [dict(row) for row in rows]
    
    def get_repo_subscribers(self, repo_full_name: str) -> List[int]:
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''SELECT chat_id FROM repositories 
                        WHERE repo_full_name = ?''', (repo_full_name,))
            rows = c.fetchall()
            conn.close()
            return [row[0] for row in rows]
    
    def update_last_commit(self, repo_full_name: str, commit_sha: str, commit_date: datetime):
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''UPDATE repositories 
                        SET last_commit_sha = ?, 
                            last_commit_date = ?,
                            last_check = ?
                        WHERE repo_full_name = ?''',
                     (commit_sha, commit_date, datetime.now(), repo_full_name))
            conn.commit()
            conn.close()
    
    def log_commit(self, commit_data: Dict):
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''INSERT INTO commit_history 
                        (repo_full_name, commit_sha, commit_message, 
                         author_name, author_email, commit_date, commit_url,
                         added, removed, modified)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                     (commit_data['repo_full_name'],
                      commit_data['sha'],
                      commit_data['message'],
                      commit_data['author_name'],
                      commit_data['author_email'],
                      commit_data['date'],
                      commit_data['url'],
                      commit_data.get('added', 0),
                      commit_data.get('removed', 0),
                      commit_data.get('modified', 0)))
            conn.commit()
            conn.close()
    
    def is_commit_logged(self, repo_full_name: str, commit_sha: str) -> bool:
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''SELECT 1 FROM commit_history 
                        WHERE repo_full_name = ? AND commit_sha = ? 
                        LIMIT 1''', (repo_full_name, commit_sha))
            result = c.fetchone()
            conn.close()
            return result is not None
    
    def get_last_commit_date(self, repo_full_name: str) -> Optional[datetime]:
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''SELECT last_commit_date FROM repositories 
                        WHERE repo_full_name = ?''', (repo_full_name,))
            result = c.fetchone()
            conn.close()
            
            if result and result[0]:
                try:
                    if isinstance(result[0], str):
                        return datetime.strptime(
                            result[0], 
                            '%Y-%m-%d %H:%M:%S.%f' if '.' in result[0] else '%Y-%m-%d %H:%M:%S'
                        )
                    else:
                        return datetime.fromisoformat(str(result[0]))
                except Exception:
                    return None
            return None