import sqlite3

conn = sqlite3.connect('warning_history.db')
cursor = conn.cursor()

# 獲取所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('Tables:', tables)

# 檢查每個表的結構和記錄數
for table in tables:
    print(f'\n{table[0]}:')
    cursor.execute(f'PRAGMA table_info({table[0]})')
    cols = cursor.fetchall()
    for col in cols:
        print(f'  {col[1]} ({col[2]})')
    cursor.execute(f'SELECT COUNT(*) FROM {table[0]}')
    print(f'  Records: {cursor.fetchone()[0]}')

conn.close()
