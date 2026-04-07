import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Добавляем колонку reset_code
try:
    cursor.execute('ALTER TABLE users ADD COLUMN reset_code TEXT')
    print("✅ Добавлена колонка reset_code")
except sqlite3.OperationalError:
    print("⏩ Колонка reset_code уже существует")

# Добавляем колонку reset_code_expires
try:
    cursor.execute('ALTER TABLE users ADD COLUMN reset_code_expires DATETIME')
    print("✅ Добавлена колонка reset_code_expires")
except sqlite3.OperationalError:
    print("⏩ Колонка reset_code_expires уже существует")

conn.commit()
conn.close()

print("✅ Готово! Теперь можно перезапустить сервер.")