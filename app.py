from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.middleware.proxy_fix import ProxyFix
import os
import secrets
import re

# NOTE: JavaRunner will NOT work on Vercel because Vercel environments 
# do not have the Java Development Kit (JDK) installed.
# You would need to use an external API (like JDoodle or Piston) to compile code.
# from java_runner import JavaRunner 
# java_runner = JavaRunner()

# Initialize Flask app
app = Flask(__name__)

# --- CONFIGURATION ---
# 1. Secret Key
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    SECRET_KEY = secrets.token_hex(16)
app.config['SECRET_KEY'] = SECRET_KEY

# 2. Session Security
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# 3. Database
# Vercel requires PostgreSQL. SQLite files are deleted when the server sleeps.
DATABASE_URL = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')
if DATABASE_URL:
    if "postgres://" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    # Local fallback
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///javamastery.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 4. Mail Config
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', 'on', '1']
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

# --- EXTENSIONS ---
# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
mail = Mail(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Apply ProxyFix for Vercel
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- MODELS ---
# (Keep your existing models exactly as they are. I have condensed them for brevity here, 
# but in your file, PASTE YOUR FULL MODEL CLASSES HERE: User, Lesson, Course, etc.)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(20), default='student')
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    totp_secret = db.Column(db.String(32))
    is_2fa_enabled = db.Column(db.Boolean, default=False)
    
    # Relationships (simplified for the fix, ensure your full models are here)
    progress = db.relationship('Progress', backref='user', lazy=True)
    achievements = db.relationship('Achievement', backref='user', lazy=True)
    enrollments = db.relationship('Enrollment', backref='user', lazy=True)
    # Add other relationships...

    def is_admin(self): return self.role == 'admin'
    def is_instructor(self): return self.role == 'instructor'
    def is_student(self): return self.role == 'student'

# ... [PASTE ALL OTHER MODELS HERE: Lesson, Course, Progress, Achievement, Quiz, etc.] ...
# To save space in this answer, I am assuming you keep your existing model classes.
# Just make sure they are defined before db.create_all() is called.

# --- UTILS ---
def generate_token():
    return secrets.token_urlsafe(32)

def validate_password_strength(password):
    return True, "Strong" # Simplified for brevity

def send_reset_email(user):
    return True # Simplified

def verify_reset_token(token):
    return None

# --- DECORATORS ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            return jsonify({'success': False, 'message': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# --- ROUTES ---

@app.route('/')
def home():
    # Wrap in try/except to prevent DB crash on first load if tables don't exist
    try:
        courses = Course.query.all()
    except:
        courses = []
    return render_template('index.html', courses=courses)

# ... [PASTE ALL YOUR ROUTES HERE] ...
# Login, Register, Dashboard, etc.

# --- JAVA RUNNER FIX ---
@app.route('/api/run_code', methods=['POST'])
def run_code():
    """
    MOCK implementation for Vercel. 
    Real Java compilation requires an external API (like Piston or JDoodle).
    """
    return jsonify({
        'success': False, 
        'output': '', 
        'error': 'Java compilation is disabled in this Vercel environment. You need an external compiler API.'
    })

# --- DATABASE INITIALIZATION ---
# CRITICAL: Do not run this globally. Run this only when you visit /init_db
@app.route('/init_db')
def initialize_database():
    try:
        db.create_all()
        # Add your init_sample_data() logic here if you want
        return jsonify({'success': True, 'message': 'Database initialized!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# --- ENTRY POINT ---
# This must be at the very bottom
if __name__ == '__main__':
    app.run(debug=True)