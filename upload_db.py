import sqlite3

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute("ALTER TABLE notes ADD COLUMN course TEXT")

conn.commit()
conn.close()

print("Course column added successfully!")