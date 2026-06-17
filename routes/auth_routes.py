# routes/auth_routes.py
# Handles registration, login, logout for students and admin

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models.db_helper import fetch_one, execute_query

auth_bp = Blueprint('auth', __name__)

# ── Home / Landing Page ───────────────────────────────────────
@auth_bp.route('/')
def index():
    return render_template('index.html')

# ── Student Registration ──────────────────────────────────────
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')
        college  = request.form.get('college', '').strip()
        skills   = request.form.get('skills', '').strip()

        # Basic validation
        if not all([name, email, password, college]):
            flash('All fields are required.', 'danger')
            return render_template('register.html')

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('register.html')

        # Check if email already exists
        existing = fetch_one("SELECT candidate_id FROM candidates WHERE email = %s", (email,))
        if existing:
            flash('Email is already registered. Please login.', 'warning')
            return redirect(url_for('auth.login'))

        # Hash password and insert
        hashed_pw = generate_password_hash(password)
        execute_query(
            "INSERT INTO candidates (name, email, password, college, skills) VALUES (%s,%s,%s,%s,%s)",
            (name, email, hashed_pw, college, skills)
        )
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')

# ── Student Login ─────────────────────────────────────────────
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'candidate_id' in session:
        return redirect(url_for('student.dashboard'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        candidate = fetch_one(
            "SELECT candidate_id, name, password FROM candidates WHERE email = %s", (email,)
        )

        if candidate and check_password_hash(candidate[2], password):
            session['candidate_id'] = candidate[0]
            session['candidate_name'] = candidate[1]
            session['role'] = 'student'
            flash(f'Welcome back, {candidate[1]}! 👋', 'success')
            return redirect(url_for('student.dashboard'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')

# ── Admin Login ───────────────────────────────────────────────
@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if 'admin_id' in session:
        return redirect(url_for('admin.admin_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        admin = fetch_one(
            "SELECT admin_id, username, password FROM admins WHERE username = %s", (username,)
        )

        # Admin password check (supports both hashed and plain for initial setup)
        if admin:
            pw_match = False
            try:
                pw_match = check_password_hash(admin[2], password)
            except Exception:
                pw_match = (admin[2] == password)

            if pw_match:
                session['admin_id'] = admin[0]
                session['admin_name'] = admin[1]
                session['role'] = 'admin'
                flash('Admin login successful!', 'success')
                return redirect(url_for('admin.admin_dashboard'))

        flash('Invalid admin credentials.', 'danger')

    return render_template('admin_login.html')

# ── Logout ────────────────────────────────────────────────────
@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.index'))
