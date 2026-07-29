import sqlite3

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(notes)")
print(cursor.fetchall())

conn.close()