import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()

# Voeg kolom toe als hij nog niet bestaat
try:
    c.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
    conn.commit()
    print("✅ Kolom 'is_admin' toegevoegd.")
except sqlite3.OperationalError as e:
    print(f"⚠️ Fout of kolom bestaat al: {e}")

conn.close()