import sqlite3

DB = '../database.db'

def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    return any(col[1] == column for col in cursor.fetchall())

def migrate():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    if not column_exists(c, 'users', 'email'):
        print("🛠 Voeg kolom 'email' toe aan users-tabel...")
        c.execute("ALTER TABLE users ADD COLUMN email TEXT")

    if not column_exists(c, 'users', 'address'):
        print("🛠 Voeg kolom 'address' toe aan users-tabel...")
        c.execute("ALTER TABLE users ADD COLUMN address TEXT")

    conn.commit()
    conn.close()
    print("✅ Migratie voltooid.")

if __name__ == '__main__':
    migrate()
