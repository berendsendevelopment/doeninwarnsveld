import sqlite3

conn = sqlite3.connect('../database.db')
c = conn.cursor()
c.execute("ALTER TABLE activities ADD COLUMN link TEXT;")
conn.commit()
conn.close()