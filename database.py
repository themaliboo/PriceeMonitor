import sqlite3
from datetime import datetime, timedelta
import hashlib
import secrets
import random
import string


class Database:
    def __init__(self, db_path='database.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.init_tables()

    def init_tables(self):
        cursor = self.conn.cursor()

        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                password_hash TEXT,
                salt TEXT,
                api_key TEXT UNIQUE,
                full_name TEXT,
                phone TEXT,
                created_at DATETIME,
                subscription_end DATE,
                subscription_type TEXT DEFAULT 'free',
                is_active BOOLEAN DEFAULT 0,
                is_verified BOOLEAN DEFAULT 0,
                verification_code TEXT,
                reset_code TEXT,
                reset_code_expires DATETIME,
                free_requests_used INTEGER DEFAULT 0,
                total_requests INTEGER DEFAULT 0,
                email_notifications BOOLEAN DEFAULT 1,
                telegram_notifications BOOLEAN DEFAULT 0,
                telegram_chat_id TEXT
            )
        ''')

        # Таблица платежей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                payment_id TEXT UNIQUE,
                amount INTEGER,
                status TEXT,
                payment_method TEXT,
                created_at DATETIME,
                paid_at DATETIME,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')

        # Таблица конкурентов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_competitors (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                name TEXT,
                platform TEXT,
                url TEXT,
                my_price REAL,
                created_at DATETIME,
                last_check DATETIME,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')

        # Таблица истории парсинга
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS parse_history (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                competitor_id INTEGER,
                result_price REAL,
                result_stock INTEGER,
                created_at DATETIME,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(competitor_id) REFERENCES user_competitors(id)
            )
        ''')

        # Таблица задач автопарсинга
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_tasks (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                competitor_id INTEGER,
                task_name TEXT,
                schedule_time TEXT,
                schedule_days TEXT,
                is_active BOOLEAN DEFAULT 1,
                last_run DATETIME,
                next_run DATETIME,
                created_at DATETIME,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(competitor_id) REFERENCES user_competitors(id)
            )
        ''')

        # Таблица логов авто-парсинга
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS auto_parse_logs (
                id INTEGER PRIMARY KEY,
                task_id INTEGER,
                competitor_name TEXT,
                result_price REAL,
                result_stock INTEGER,
                status TEXT,
                error_message TEXT,
                created_at DATETIME,
                FOREIGN KEY(task_id) REFERENCES scheduled_tasks(id)
            )
        ''')

        # Таблица виджетов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS widgets (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                competitor_id INTEGER,
                widget_code TEXT UNIQUE,
                theme TEXT,
                views INTEGER DEFAULT 0,
                created_at DATETIME,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(competitor_id) REFERENCES user_competitors(id)
            )
        ''')

        # Таблица настроек Telegram
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS telegram_settings (
                user_id INTEGER PRIMARY KEY,
                telegram_chat_id TEXT,
                notifications_enabled BOOLEAN DEFAULT 1,
                bind_date DATETIME,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')

        self.conn.commit()

    def generate_verification_code(self):
        return ''.join(random.choices(string.digits, k=6))

    def register_user(self, email, password, full_name='', phone=''):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        if cursor.fetchone():
            return None, "Email уже зарегистрирован"

        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
        api_key = secrets.token_urlsafe(32)
        verification_code = self.generate_verification_code()

        cursor.execute('''
            INSERT INTO users (email, password_hash, salt, api_key, full_name, phone, created_at, verification_code, free_requests_used, total_requests, is_verified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (email, password_hash, salt, api_key, full_name, phone, datetime.now(), verification_code, 0, 0, 0))

        user_id = cursor.lastrowid
        self.conn.commit()
        return user_id, verification_code

    def verify_email(self, email, code):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, verification_code FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()

        if user and user[1] == code:
            cursor.execute('UPDATE users SET is_verified = 1, verification_code = NULL WHERE id = ?', (user[0],))
            self.conn.commit()
            return True
        return False

    def verify_user(self, email, password):
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT id, password_hash, salt, is_active, is_verified, subscription_end, free_requests_used FROM users WHERE email = ?',
            (email,))
        user = cursor.fetchone()

        if not user:
            return None, "Пользователь не найден"

        if not user[4]:
            return None, "Подтвердите email. Проверьте почту."

        test_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), user[2].encode(), 100000).hex()
        if test_hash != user[1]:
            return None, "Неверный пароль"

        has_access = False
        if user[3]:
            if user[5] and datetime.strptime(user[5], '%Y-%m-%d').date() >= datetime.now().date():
                has_access = True

        return {
            'id': user[0],
            'email': email,
            'has_subscription': has_access,
            'free_requests_used': user[6],
            'is_verified': user[4]
        }, None

    def set_reset_code(self, email, code):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET reset_code = ?, reset_code_expires = ? WHERE email = ?',
                       (code, datetime.now() + timedelta(minutes=15), email))
        self.conn.commit()

    def verify_reset_code(self, email, code):
        cursor = self.conn.cursor()
        cursor.execute('SELECT reset_code, reset_code_expires FROM users WHERE email = ?', (email,))
        result = cursor.fetchone()

        if result and result[0] == code and result[1] and datetime.now() < datetime.strptime(result[1],
                                                                                             '%Y-%m-%d %H:%M:%S.%f'):
            return True
        return False

    def reset_password(self, email, new_password):
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', new_password.encode(), salt.encode(), 100000).hex()

        cursor = self.conn.cursor()
        cursor.execute(
            'UPDATE users SET password_hash = ?, salt = ?, reset_code = NULL, reset_code_expires = NULL WHERE email = ?',
            (password_hash, salt, email))
        self.conn.commit()

    def can_make_request(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT is_active, subscription_end, free_requests_used FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()

        if not user:
            return False, "Пользователь не найден"

        if user[0] and user[1] and datetime.strptime(user[1], '%Y-%m-%d').date() >= datetime.now().date():
            return True, "active_subscription"

        if user[2] < 1:
            return True, "free_request"

        return False, "Бесплатный запрос использован. Оформите подписку."

    def use_request(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT is_active, free_requests_used FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()

        if user and user[0]:
            cursor.execute('UPDATE users SET total_requests = total_requests + 1 WHERE id = ?', (user_id,))
        else:
            cursor.execute('UPDATE users SET free_requests_used = free_requests_used + 1 WHERE id = ?', (user_id,))

        self.conn.commit()

    def get_user_profile(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT email, full_name, phone, created_at, subscription_end, subscription_type, 
                   total_requests, email_notifications, telegram_notifications, api_key
            FROM users WHERE id = ?
        ''', (user_id,))
        user = cursor.fetchone()

        if user:
            return {
                'email': user[0],
                'full_name': user[1] or '',
                'phone': user[2] or '',
                'registered_at': user[3].strftime('%d.%m.%Y') if user[3] else '',
                'subscription_end': user[4] if user[4] else '—',
                'subscription_type': user[5] or 'free',
                'total_requests': user[6] or 0,
                'email_notifications': bool(user[7]),
                'telegram_notifications': bool(user[8]),
                'api_key': user[9]
            }
        return None

    def update_profile(self, user_id, full_name=None, phone=None):
        cursor = self.conn.cursor()
        if full_name is not None:
            cursor.execute('UPDATE users SET full_name = ? WHERE id = ?', (full_name, user_id))
        if phone is not None:
            cursor.execute('UPDATE users SET phone = ? WHERE id = ?', (phone, user_id))
        self.conn.commit()

    def get_competitors(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT id, name, platform, url, my_price FROM user_competitors WHERE user_id = ? ORDER BY created_at DESC',
            (user_id,))
        competitors = []
        for row in cursor.fetchall():
            cursor.execute(
                'SELECT result_price FROM parse_history WHERE competitor_id = ? ORDER BY created_at DESC LIMIT 1',
                (row[0],))
            last_price = cursor.fetchone()
            competitors.append({
                'id': row[0], 'name': row[1], 'platform': row[2], 'url': row[3], 'my_price': row[4],
                'current_price': last_price[0] if last_price else None
            })
        return competitors

    def add_competitor(self, user_id, name, platform, url, my_price=0):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO user_competitors (user_id, name, platform, url, my_price, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, name, platform, url, my_price, datetime.now()))
        comp_id = cursor.lastrowid
        self.conn.commit()
        return comp_id

    def delete_competitor(self, comp_id, user_id):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM user_competitors WHERE id = ? AND user_id = ?', (comp_id, user_id))
        self.conn.commit()

    def save_parse_result(self, user_id, competitor_id, price, stock=None):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO parse_history (user_id, competitor_id, result_price, result_stock, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, competitor_id, price, stock, datetime.now()))
        cursor.execute('UPDATE user_competitors SET last_check = ? WHERE id = ?', (datetime.now(), competitor_id))
        self.conn.commit()

    def get_history(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT ph.created_at, uc.name, uc.platform, ph.result_price
            FROM parse_history ph
            JOIN user_competitors uc ON ph.competitor_id = uc.id
            WHERE ph.user_id = ?
            ORDER BY ph.created_at DESC LIMIT 50
        ''', (user_id,))
        history = [{'date': row[0], 'name': row[1], 'platform': row[2], 'price': row[3]} for row in cursor.fetchall()]
        return history

    def get_stats(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM user_competitors WHERE user_id = ?', (user_id,))
        total_competitors = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM parse_history WHERE user_id = ?', (user_id,))
        total_parses = cursor.fetchone()[0]
        cursor.execute('SELECT free_requests_used FROM users WHERE id = ?', (user_id,))
        free_used = cursor.fetchone()[0]
        return {'total_competitors': total_competitors, 'total_parses': total_parses, 'free_used': free_used}