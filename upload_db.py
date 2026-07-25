import sqlite3

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute("ALTER TABLE notes ADD COLUMN upload_date TEXT")

conn.commit()
conn.close()

print("Column added successfully!")