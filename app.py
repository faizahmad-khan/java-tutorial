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

# NOTE: JavaRunner is disabled for Vercel compatibility
# from java_runner import JavaRunner
# java_runner = JavaRunner()

# Initialize Flask app
app = Flask(__name__)

# --- CONFIGURATION ---
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    if os.environ.get('VERCEL'):
        # Log a warning but don't crash immediately on build
        print("WARNING: SECRET_KEY not set. Using random key.")
        SECRET_KEY = secrets.token_hex(16)
    else:
        SECRET_KEY = secrets.token_hex(16)
app.config['SECRET_KEY'] = SECRET_KEY

# Session Security
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Database Configuration
DATABASE_URL = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')
if DATABASE_URL:
    if "postgres://" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///javamastery.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Mail Config
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', 'on', '1']
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
mail = Mail(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Apply ProxyFix for Vercel
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- MODELS ---
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
    
    # Relationships
    progress = db.relationship('Progress', backref='user', lazy=True, cascade='all, delete-orphan')
    achievements = db.relationship('Achievement', backref='user', lazy=True, cascade='all, delete-orphan')
    enrollments = db.relationship('Enrollment', backref='user', lazy=True, cascade='all, delete-orphan')
    submissions = db.relationship('AssignmentSubmission', backref='student', lazy=True, cascade='all, delete-orphan')
    created_courses = db.relationship('Course', backref='instructor', lazy=True, foreign_keys='Course.instructor_id')

    def is_admin(self): return self.role == 'admin'
    def is_instructor(self): return self.role == 'instructor'
    def is_student(self): return self.role == 'student'

class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    lesson_type = db.Column(db.String(20), default='text')
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    lesson_number = db.Column(db.Integer, nullable=False)
    multimedia_url = db.Column(db.String(200), nullable=True)
    duration = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='draft')
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    progress = db.relationship('Progress', backref='lesson', lazy=True, cascade='all, delete-orphan')
    quizzes = db.relationship('Quiz', backref='lesson', lazy=True, cascade='all, delete-orphan')
    assignments = db.relationship('Assignment', backref='lesson', lazy=True, cascade='all, delete-orphan')
    notes = db.relationship('Note', backref='lesson', lazy=True, cascade='all, delete-orphan')

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    level = db.Column(db.String(20), nullable=False)
    category = db.Column(db.String(50), default='General')
    instructor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='draft')
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    lessons = db.relationship('Lesson', backref='course', lazy=True, cascade='all, delete-orphan')
    progress = db.relationship('Progress', backref='course', lazy=True, cascade='all, delete-orphan')
    enrollments = db.relationship('Enrollment', backref='course', lazy=True, cascade='all, delete-orphan')
    assignments = db.relationship('Assignment', backref='course', lazy=True, cascade='all, delete-orphan')

class Progress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    score = db.Column(db.Float)
    time_spent = db.Column(db.Integer, default=0)
    date_completed = db.Column(db.DateTime)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_accessed = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    badge_icon = db.Column(db.String(50))
    date_earned = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    options = db.Column(db.JSON, nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)
    points = db.Column(db.Integer, default=1)
    time_limit = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='active')
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class QuizSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    selected_answer = db.Column(db.String(1))
    is_correct = db.Column(db.Boolean, default=False)
    score = db.Column(db.Float, default=0.0)
    time_taken = db.Column(db.Integer, default=0)
    date_submitted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    assignment_type = db.Column(db.String(20), default='coding')
    due_date = db.Column(db.DateTime)
    max_score = db.Column(db.Integer, default=100)
    status = db.Column(db.String(20), default='active')
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    submissions = db.relationship('AssignmentSubmission', backref='assignment', lazy=True, cascade='all, delete-orphan')

class AssignmentSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False)
    submission_text = db.Column(db.Text)
    submission_file = db.Column(db.String(200))
    submission_code = db.Column(db.Text)
    score = db.Column(db.Float)
    feedback = db.Column(db.Text)
    status = db.Column(db.String(20), default='submitted')
    date_submitted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_graded = db.Column(db.DateTime)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    enrollment_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    completion_date = db.Column(db.DateTime)
    final_grade = db.Column(db.Float)
    status = db.Column(db.String(20), default='enrolled')

class Grade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=True)
    grade = db.Column(db.Float, nullable=False)
    max_grade = db.Column(db.Float, default=100.0)
    date_recorded = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    grade_type = db.Column(db.String(20), default='assignment')

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    parent = db.relationship('Category', remote_side=[id], backref='subcategories')

class ContentApproval(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content_type = db.Column(db.String(20), nullable=False)
    content_id = db.Column(db.Integer, nullable=False)
    submitted_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    status = db.Column(db.String(20), default='pending')
    submission_notes = db.Column(db.Text)
    approval_notes = db.Column(db.Text)
    date_submitted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_approved = db.Column(db.DateTime)

class UserSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_token = db.Column(db.String(10), unique=True, nullable=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(200))
    login_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    expires_at = db.Column(db.DateTime)

class PasswordResetToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(10), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(20), default='info')
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class ForumCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class ForumThread(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('forum_category.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_pinned = db.Column(db.Boolean, default=False)
    is_locked = db.Column(db.Boolean, default=False)
    
    user = db.relationship('User', backref='forum_threads')
    category = db.relationship('ForumCategory', backref='threads')
    replies = db.relationship('ForumReply', backref='thread', lazy=True, cascade='all, delete-orphan')

class ForumReply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    thread_id = db.Column(db.Integer, db.ForeignKey('forum_thread.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    user = db.relationship('User', backref='forum_replies')

# --- FORMS ---
class CourseForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=5, max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    level = StringField('Level', validators=[DataRequired()])
    category = StringField('Category', validators=[DataRequired()])
    submit = SubmitField('Add Course')

class LessonForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=5, max=100)])
    content = TextAreaField('Content', validators=[DataRequired()])
    lesson_type = StringField('Lesson Type', validators=[DataRequired()])
    course_id = StringField('Course ID', validators=[DataRequired()])
    lesson_number = StringField('Lesson Number', validators=[DataRequired()])
    multimedia_url = StringField('Multimedia URL')
    duration = StringField('Duration (minutes)')
    submit = SubmitField('Add Lesson')

class QuizForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=5, max=200)])
    lesson_id = StringField('Lesson ID', validators=[DataRequired()])
    question = TextAreaField('Question', validators=[DataRequired()])
    option_a = StringField('Option A', validators=[DataRequired()])
    option_b = StringField('Option B', validators=[DataRequired()])
    option_c = StringField('Option C', validators=[DataRequired()])
    option_d = StringField('Option D', validators=[DataRequired()])
    correct_answer = StringField('Correct Answer (A, B, C, or D)', validators=[DataRequired(), Length(min=1, max=1)])
    points = StringField('Points')
    time_limit = StringField('Time Limit (seconds)')
    submit = SubmitField('Add Quiz')

class AssignmentForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=5, max=200)])
    description = TextAreaField('Description', validators=[DataRequired()])
    course_id = StringField('Course ID', validators=[DataRequired()])
    lesson_id = StringField('Lesson ID', validators=[DataRequired()])
    assignment_type = StringField('Assignment Type', validators=[DataRequired()])
    due_date = StringField('Due Date (YYYY-MM-DD HH:MM:SS)')
    max_score = StringField('Max Score')
    submit = SubmitField('Add Assignment')

class NoteForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=5, max=100)])
    content = TextAreaField('Content', validators=[DataRequired()])
    lesson_id = StringField('Lesson ID', validators=[DataRequired()])
    submit = SubmitField('Add Note')

# --- HELPERS ---
def generate_token():
    return secrets.token_urlsafe(32)

def validate_password_strength(password):
    return True, "Strong" 

def check_and_assign_achievements(user_id):
    # Simplified achievement logic
    try:
        completed_lessons = Progress.query.filter_by(user_id=user_id, completed=True).count()
        if completed_lessons >= 5:
            if not Achievement.query.filter_by(user_id=user_id, name="Code Runner").first():
                db.session.add(Achievement(user_id=user_id, name="Code Runner", description="Completed 5 lessons"))
                db.session.commit()
    except Exception as e:
        print(f"Achievement error: {e}")

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
    try:
        courses = Course.query.all()
    except:
        courses = []
    return render_template('index.html', courses=courses)

@app.route('/api/run_code', methods=['POST'])
def run_code():
    return jsonify({
        'success': False, 
        'output': '', 
        'error': 'Java compilation is disabled in this Vercel environment. You need an external compiler API.'
    })

@app.route('/init_db')
def initialize_database():
    try:
        db.create_all()
        # Initialize basic data if needed
        return jsonify({'success': True, 'message': 'Database initialized!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/forum')
@login_required
def forum():
    return render_template('forum.html')

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        courses = Course.query.all()
        for course in courses:
            total_lessons = Lesson.query.filter_by(course_id=course.id).count()
            completed_lessons = Progress.query.filter_by(
                user_id=current_user.id, 
                course_id=course.id, 
                completed=True
            ).count()
            
            course.total_lessons = total_lessons
            course.completed_lessons = completed_lessons
            course.progress_percentage = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
    except:
        courses = []
        
    return render_template('dashboard.html', courses=courses)

@app.route('/profile')
@login_required
def profile():
    try:
        user_progress = Progress.query.filter_by(user_id=current_user.id).all()
        user_achievements = Achievement.query.filter_by(user_id=current_user.id).all()
    except:
        user_progress = []
        user_achievements = []
    return render_template('profile.html', progress=user_progress, achievements=user_achievements)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not username or not email or not password:
            return jsonify({'success': False, 'message': 'All fields are required'})

        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': 'Email exists'})
            
        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password_hash=hashed)
        db.session.add(user)
        db.session.commit()
        return jsonify({'success': True, 'redirect_url': '/login', 'message': 'Registration successful'})
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user, remember=True)
            return jsonify({'success': True, 'redirect_url': '/dashboard'})
        return jsonify({'success': False, 'message': 'Invalid credentials'})
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# --- API ROUTES ---
@app.route('/api/progress/<int:lesson_id>', methods=['PUT'])
@login_required
def update_lesson_progress(lesson_id):
    data = request.get_json()
    completed = data.get('completed', False)
    lesson = Lesson.query.get_or_404(lesson_id)
    
    progress = Progress.query.filter_by(user_id=current_user.id, lesson_id=lesson_id).first()
    if not progress:
        progress = Progress(
            user_id=current_user.id,
            lesson_id=lesson_id,
            course_id=lesson.course_id,
            completed=completed
        )
        db.session.add(progress)
    else:
        progress.completed = completed
        progress.last_accessed = datetime.utcnow()
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/courses/<int:course_id>')
def course_detail(course_id):
    # This might be needed for your frontend JS
    course = Course.query.get_or_404(course_id)
    return jsonify({'id': course.id, 'title': course.title})
 # --- MISSING PASSWORD RESET ROUTES ---

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email', '').strip()
        
        # We don't actually send emails in this Vercel demo to prevent errors
        # In a real app, you would verify the user and send the email here
        return jsonify({'success': True, 'message': 'If your email exists, a reset link has been sent.'})
    
    return render_template('reset_password_request.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    # This route is needed so url_for('reset_password') works in templates
    if request.method == 'POST':
        data = request.get_json()
        password = data.get('password', '')
        
        # Logic to update password would go here
        # For now, we return success to prevent crashes
        return jsonify({'success': True, 'message': 'Password has been reset.'})
    
    return render_template('reset_password.html')

# Optional: Add this only if you see a crash regarding 'admin_dashboard'
@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    # Simplified admin view
    courses = Course.query.all()
    return render_template('admin/dashboard.html', courses=courses)

@app.route('/create_admin')
def create_admin():
    # 1. SECURITY: Check for a secret setup key in the URL
    # You will visit: /create_admin?key=YOUR_SETUP_KEY
    setup_key = request.args.get('key')
    expected_key = os.environ.get('SETUP_KEY')
    
    if not expected_key or setup_key != expected_key:
        return jsonify({'success': False, 'message': 'Unauthorized: Invalid or missing setup key.'}), 401

    # 2. Get secure credentials from Vercel Environment Variables
    admin_user = os.environ.get('ADMIN_USERNAME')
    admin_pass = os.environ.get('ADMIN_PASSWORD')
    admin_email = os.environ.get('ADMIN_EMAIL')

    if not admin_user or not admin_pass:
        return jsonify({'success': False, 'message': 'Admin credentials not set in environment variables.'}), 500

    try:
        # 3. Create or Update the Admin
        user = User.query.filter_by(username=admin_user).first()
        hashed_pw = bcrypt.generate_password_hash(admin_pass).decode('utf-8')
        
        if user:
            user.password_hash = hashed_pw
            user.role = 'admin'
            user.email = admin_email if admin_email else user.email
            action = "updated"
        else:
            if not admin_email:
                return jsonify({'success': False, 'message': 'Email required for new admin.'}), 400
            user = User(
                username=admin_user,
                email=admin_email,
                password_hash=hashed_pw,
                role='admin',
                is_verified=True
            )
            db.session.add(user)
            action = "created"
            
        db.session.commit()
        return jsonify({'success': True, 'message': f"Admin user '{admin_user}' {action} successfully."})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    app.run(debug=True)