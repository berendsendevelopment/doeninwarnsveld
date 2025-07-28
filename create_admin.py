import sqlite3
from werkzeug.security import generate_password_hash

DB = 'database.db'

def create_admin():
    username = 'admin'
    password = 'admin123'  # wijzig dit na eerste inloggen!
    hashed_password = generate_password_hash(password)
    organization = 'Berendsen Development'

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    try:
        c.execute(
            "INSERT INTO users (username, password, organization, is_admin) VALUES (?, ?, ?, ?)",
            (username, hashed_password, organization, 1)
        )
        conn.commit()
        print("✅ Admingebruiker aangemaakt.")
    except sqlite3.IntegrityError:
        print("⚠️ Gebruiker bestaat al.")

    conn.close()

if __name__ == '__main__':
    create_admin()
