from flask import Flask, render_template, redirect, url_for, request, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
import psycopg2
import os

def get_db_connection():
    return psycopg2.connect(
        host=os.environ.get('POSTGRES_HOST', '146.190.225.16'),
        database=os.environ.get('POSTGRES_DB', 'doeninwarnsveld_db'),
        user=os.environ.get('POSTGRES_USER', 'doeninwarnsveld_dbu'),
        password=os.environ.get('POSTGRES_PASSWORD', 'Berendsendevelopment2025!')
    )

app = Flask(__name__)
app.secret_key = os.urandom(24)
DB = 'database.db'

# -----------------------------
# Database Setup (1x uitvoeren)
# -----------------------------
def init_db():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                       id SERIAL PRIMARY KEY,
                        username TEXT,
                        password TEXT,
                        organization TEXT,
                        is_admin BOOLEAN DEFAULT FALSE,
                        email TEXT,
                        address TEXT)''')

        c.execute('''CREATE TABLE IF NOT EXISTS activities (
                        id SERIAL PRIMARY KEY,
                        title TEXT,
                        date TEXT,
                        description TEXT,
                        organization TEXT)''')

        c.execute('''CREATE TABLE IF NOT EXISTS vacancies (
                        id SERIAL PRIMARY KEY,
                        title TEXT,
                        organization TEXT,
                        description TEXT)''')

        c.execute('''CREATE TABLE IF NOT EXISTS supplies (
                        id SERIAL PRIMARY KEY,
                        organization TEXT,
                        item TEXT,
                        quantity INTEGER)''')

        c.execute('''CREATE TABLE IF NOT EXISTS knowledgebase (
                        id SERIAL PRIMARY KEY,
                        title TEXT,
                        content TEXT,
                        author_org TEXT,
                        created_at TEXT)''')

        c.execute('''CREATE TABLE IF NOT EXISTS civil_contacts (
                        id SERIAL PRIMARY KEY,
                        name TEXT,
                        role TEXT,
                        email TEXT)''')

init_db()

# ------------------
# Public routes
# ------------------
@app.route('/')
def home():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT title, date, description FROM activities ORDER BY date ASC")
    activities = c.fetchall()
    c.execute("SELECT title, organization, description FROM vacancies")
    vacancies = c.fetchall()
    conn.close()
    return render_template('public.html', activities=activities, vacancies=vacancies)

# ------------------
# Authentication
# ------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = c.fetchone()
        conn.close()
        if user and check_password_hash(user[2], password):
            session['user'] = username
            session['org'] = user[3]
            session['is_admin'] = bool(user[4])
            return redirect(url_for('dashboard'))
        flash('Ongeldige inloggegevens')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/admin/users', methods=['GET', 'POST'])
def manage_users():
    if not session.get('is_admin'):
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    c = conn.cursor()

    if request.method == 'POST':
        if 'delete' in request.form:
            c.execute("DELETE FROM users WHERE id = %s", (request.form['delete'],))
        else:
            username = request.form['username']
            password = generate_password_hash(request.form['password'])
            organization = request.form['organization']
            is_admin = True if request.form.get('is_admin') else False
            try:
                c.execute("""
                    INSERT INTO users (username, password, organization, is_admin)
                    VALUES (%s, %s, %s, %s)
                """, (username, password, organization, is_admin))
            except errors.UniqueViolation:
                conn.rollback()
                flash("Gebruikersnaam bestaat al.")
        conn.commit()

    c.execute("SELECT id, username, organization, is_admin FROM users")
    users = c.fetchall()
    conn.close()
    return render_template('admin_users.html', users=users)

# ------------------
# Dashboard & Data Routes
# ------------------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM supplies")
    supplies_all = c.fetchall()
    conn.close()
    return render_template('dashboard.html', supplies_all=supplies_all)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    c = conn.cursor()

    if request.method == 'POST':
        email = request.form['email']
        address = request.form['address']
        password = request.form['password']
        confirm = request.form['confirm']

        if password and password != confirm:
            flash('Wachtwoorden komen niet overeen.')
            return redirect(url_for('profile'))

        if password:
            from werkzeug.security import generate_password_hash
            hashed = generate_password_hash(password)
            c.execute("UPDATE users SET email=%s, address=%s, password=%s WHERE username=%s",
                      (email, address, hashed, session['user']))
        else:
            c.execute("UPDATE users SET email=%s, address=%s WHERE username=%s",
                      (email, address, session['user']))
        conn.commit()
        flash('Profiel bijgewerkt.')

    c.execute("SELECT * FROM users WHERE username=%s", (session['user'],))
    user = c.fetchone()
    conn.close()
    return render_template('profiel.html', user=user)

@app.route('/activities', methods=['GET', 'POST'])
def activities():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    c = conn.cursor()
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        # Corrigeer en valideer de datum
        try:
            date_raw = request.form['date']
            parsed_date = datetime.strptime(date_raw, '%Y-%m-%d')  # verwachte HTML date input
            date = parsed_date.strftime('%Y-%m-%d')
        except ValueError:
            flash('Ongeldig datumformaat. Gebruik JJJJ-MM-DD.')
            return redirect(url_for('activities'))
        
        c.execute("INSERT INTO activities (title, date, description, organization) VALUES (%s, %s, %s, %s)",
                  (title, date, description, session['org']))
        conn.commit()
    c.execute("SELECT * FROM activities ORDER BY date ASC")
    activities = c.fetchall()
    conn.close()
    return render_template('activities.html', activities=activities)

@app.route('/activities/edit/<int:id>', methods=['GET', 'POST'])
def edit_activity(id):
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    c = conn.cursor()

    if request.method == 'POST':
        title = request.form['title']
        date = request.form['date']
        description = request.form['description']
        c.execute("UPDATE activities SET title=%s, date=%s, description=%s WHERE id=%s AND organization=%s",
                  (title, date, description, id, session['org']))
        conn.commit()
        conn.close()
        return redirect(url_for('activities'))

    c.execute("SELECT * FROM activities WHERE id=%s AND organization=%s", (id, session['org']))
    activity = c.fetchone()
    conn.close()

    if not activity:
        flash('Geen toegang tot deze activiteit')
        return redirect(url_for('activities'))

    return render_template('edit_activity.html', activity=activity)

@app.route('/activities/delete/<int:id>', methods=['POST'])
def delete_activity(id):
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM activities WHERE id=%s AND organization=%s", (id, session['org']))
    conn.commit()
    conn.close()

    return redirect(url_for('activities'))

@app.route('/vacancies', methods=['GET', 'POST'])
def vacancies():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    c = conn.cursor()
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        c.execute("INSERT INTO vacancies (title, organization, description) VALUES (%s, %s, %s)",
                  (title, session['org'], description))
        conn.commit()
    c.execute("SELECT * FROM vacancies")
    vacancies = c.fetchall()
    conn.close()
    return render_template('vacancies.html', vacancies=vacancies)

@app.route('/vacancies/<int:id>')
def vacancy_detail(id):
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, title, description, organization FROM vacancies WHERE id=%s", (id,))
    vacancy = c.fetchone()
    conn.close()
    if not vacancy:
        flash('Vacature niet gevonden.')
        return redirect(url_for('vacancies'))
    return render_template('vacancy_detail.html', vacancy=vacancy)


@app.route('/vacancies/edit/<int:id>', methods=['GET', 'POST'])
def edit_vacancy(id):
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    c = conn.cursor()

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        c.execute("UPDATE vacancies SET title=%s, description=%s WHERE id=%s AND organization=%s", (title, description, id, session['org']))
        conn.commit()
        conn.close()
        return redirect(url_for('vacancies'))

    c.execute("SELECT * FROM vacancies WHERE id=%s AND organization=%s", (id, session['org']))
    vacancy = c.fetchone()
    conn.close()

    if not vacancy:
        flash('Vacature niet gevonden of geen rechten')
        return redirect(url_for('vacancies'))

    return render_template('edit_vacancy.html', vacancy=vacancy)

@app.route('/vacancies/delete/<int:id>', methods=['POST'])
def delete_vacancy(id):
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM vacancies WHERE id=%s AND organization=%s", (id, session['org']))
    conn.commit()
    conn.close()

    return redirect(url_for('vacancies'))

@app.route('/supplies', methods=['GET', 'POST'])
def supplies():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    c = conn.cursor()
    if request.method == 'POST':
        item = request.form['item']
        quantity = request.form['quantity']
        c.execute("INSERT INTO supplies (organization, item, quantity) VALUES (%s, %s, %s)",
                  (session['org'], item, quantity))
        conn.commit()
    c.execute("SELECT * FROM supplies")
    supplies = c.fetchall()
    conn.close()
    return render_template('supplies.html', supplies=supplies)

@app.route('/supplies/edit/<int:id>', methods=['GET', 'POST'])
def edit_supply(id):
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    c = conn.cursor()
    if request.method == 'POST':
        item = request.form['item']
        quantity = request.form['quantity']
        c.execute("UPDATE supplies SET item=%s, quantity=%s WHERE id=%s AND organization=%s",
                  (item, quantity, id, session['org']))
        conn.commit()
        conn.close()
        return redirect(url_for('supplies'))

    c.execute("SELECT * FROM supplies WHERE id=%s AND organization=%s", (id, session['org']))
    supply = c.fetchone()
    conn.close()

    if not supply:
        flash('Geen toegang tot dit voorraaditem')
        return redirect(url_for('supplies'))

    return render_template('edit_supply.html', supply=supply)

@app.route('/supplies/delete/<int:id>', methods=['POST'])
def delete_supply(id):
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM supplies WHERE id=%s AND organization=%s", (id, session['org']))
    conn.commit()
    conn.close()

    return redirect(url_for('supplies'))

@app.route('/knowledge', methods=['GET', 'POST'])
def knowledge():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    c = conn.cursor()
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        organization = session['org']
        created_at = datetime.now().strftime('%d-%m-%Y')
        c.execute("INSERT INTO knowledgebase (title, content, author_org, created_at) VALUES (%s, %s, %s, %s)",
                (title, content, organization, created_at))
        conn.commit()
    c.execute("SELECT id, title, content, author_org, created_at FROM knowledgebase ORDER BY created_at DESC")
    posts = c.fetchall()
    conn.close()
    return render_template('knowledge.html', posts=posts)

@app.route('/knowledge/<int:id>')
def knowledge_detail(id):
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, title, content, author_org, created_at FROM knowledgebase WHERE id=%s", (id,))
    post = c.fetchone()
    conn.close()
    if not post:
        flash('Bericht niet gevonden.')
        return redirect(url_for('knowledge'))
    return render_template('knowledge_detail.html', post=post)


@app.route('/knowledge/edit/<int:id>', methods=['GET', 'POST'])
def edit_knowledge(id):
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    c = conn.cursor()

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        c.execute("UPDATE knowledgebase SET title=%s, content=%s WHERE id=%s AND author_org=%s",
                  (title, content, id, session['org']))
        conn.commit()
        conn.close()
        return redirect(url_for('knowledge'))

    c.execute("SELECT * FROM knowledgebase WHERE id=%s AND author_org=%s", (id, session['org']))
    post = c.fetchone()
    conn.close()

    if not post:
        flash('Geen toegang tot dit kennisitem')
        return redirect(url_for('knowledge'))

    return render_template('edit_knowledge.html', post=post)

@app.route('/knowledge/delete/<int:id>', methods=['POST'])
def delete_knowledge(id):
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM knowledgebase WHERE id=%s AND author_org=%s", (id, session['org']))
    conn.commit()
    conn.close()

    return redirect(url_for('knowledge'))

@app.route('/contacts')
def contacts():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM civil_contacts")
    contacts = c.fetchall()
    conn.close()
    return render_template('contacts.html', contacts=contacts)

@app.route('/contacts/new', methods=['GET', 'POST'])
def new_contact():
    if 'user' not in session or not session.get('is_admin'):
        flash('Alleen beheerders mogen contacten toevoegen.')
        return redirect(url_for('contacts'))

    if request.method == 'POST':
        name = request.form['name']
        role = request.form['role']
        email = request.form['email']
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("INSERT INTO civil_contacts (name, role, email) VALUES (%s, %s, %s)", (name, role, email))
        conn.commit()
        conn.close()
        return redirect(url_for('contacts'))

    return render_template('contact_form.html')

@app.route('/contacts/edit/<int:id>', methods=['GET', 'POST'])
def edit_contact(id):
    if 'user' not in session or not session.get('is_admin'):
        flash('Alleen beheerders mogen contacten bewerken.')
        return redirect(url_for('contacts'))

    conn = get_db_connection()
    c = conn.cursor()
    if request.method == 'POST':
        name = request.form['name']
        role = request.form['role']
        email = request.form['email']
        c.execute("UPDATE civil_contacts SET name=%s, role=%s, email=%s WHERE id=%s", (name, role, email, id))
        conn.commit()
        conn.close()
        return redirect(url_for('contacts'))

    c.execute("SELECT * FROM civil_contacts WHERE id=%s", (id,))
    contact = c.fetchone()
    conn.close()
    if not contact:
        flash('Contactpersoon niet gevonden.')
        return redirect(url_for('contacts'))

    return render_template('contact_edit.html', contact=contact)

@app.route('/contacts/delete/<int:id>', methods=['POST'])
def delete_contact(id):
    if 'user' not in session or not session.get('is_admin'):
        flash('Alleen beheerders mogen contacten verwijderen.')
        return redirect(url_for('contacts'))

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM civil_contacts WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('contacts'))

@app.route('/organizations')
def organizations():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    orgs = c.fetchall()
    conn.close()
    return render_template('organizations.html', orgs=orgs)

@app.route('/api/activities')
def api_activities():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT title, date, description FROM activities")
    data = [{"title": row[0], "start": row[1], "description": row[2]} for row in c.fetchall()]
    conn.close()
    return data


# ------------------
# Run app
# ------------------
if __name__ == '__main__':
    app.run(debug=True)