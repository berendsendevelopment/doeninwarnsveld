import sqlite3

conn = sqlite3.connect('../database.db')
c = conn.cursor()
c.execute("ALTER TABLE knowledgebase ADD COLUMN created_at TEXT")
conn.commit()
conn.close()