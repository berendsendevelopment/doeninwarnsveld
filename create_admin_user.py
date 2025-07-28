import psycopg2
from werkzeug.security import generate_password_hash
import os


# Admin gegevens
username = 'admin'
password = 'admin123'
hashed_pw = generate_password_hash(password)
organization = 'Admin'
email = 'admin@example.com'
address = 'Hoofdstraat 1, Warnsveld'
is_admin = True

# Verbind met PostgreSQL
conn = psycopg2.connect(
    host=os.environ.get('POSTGRES_HOST', '146.190.225.16'),
    database=os.environ.get('POSTGRES_DB', 'doeninwarnsveld_db'),
    user=os.environ.get('POSTGRES_USER', 'doeninwarnsveld_dbu'),
    password=os.environ.get('POSTGRES_PASSWORD', 'Berendsendevelopment2025!')
)

try:
    with conn.cursor() as cursor:
        # Bestaat admin al?
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            print("⚠️  Gebruiker 'admin' bestaat al.")
        else:
            cursor.execute("""
                INSERT INTO users (username, password, organization, is_admin, email, address)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (username, hashed_pw, organization, is_admin, email, address))
            conn.commit()
            print("✅ Admin gebruiker toegevoegd.")
except Exception as e:
    print("❌ Fout bij toevoegen admin gebruiker:", e)
finally:
    conn.close()