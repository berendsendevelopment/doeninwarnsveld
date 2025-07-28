import pymysql
from werkzeug.security import generate_password_hash
import os

# Instellingen (pas aan indien nodig)
MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'woodywillem')
MYSQL_DB = os.environ.get('MYSQL_DB', 'doeninwarnsveld_dbsql')

# Admin gebruiker
username = 'admin'
password = 'admin123'
hashed_pw = generate_password_hash(password)
organization = 'Admin'
email = 'admin@example.com'
address = 'Hoofdstraat 1, Warnsveld'
is_admin = 1

# Verbinden met MySQL
conn = pymysql.connect(
    host=MYSQL_HOST,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    database=MYSQL_DB,
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

try:
    with conn.cursor() as cursor:
        # Check of gebruiker al bestaat
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            print('⚠️  Gebruiker bestaat al.')
        else:
            cursor.execute("""
                INSERT INTO users (username, password, organization, is_admin, email, address)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (username, hashed_pw, organization, is_admin, email, address))
            conn.commit()
            print('✅ Admin gebruiker succesvol toegevoegd.')
except Exception as e:
    print('❌ Fout bij toevoegen admin gebruiker:', e)
finally:
    conn.close()
