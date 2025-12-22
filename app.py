from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from datetime import datetime, timedelta
from functools import wraps
import os

import secrets
import re
from java_runner import JavaRunner

# Initialize Java runner
java_runner = JavaRunner()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(16)
# Use PostgreSQL in production, SQLite in development
import os
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    # For production (PostgreSQL)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL.replace("postgres://", "postgresql://")
else:
    # For development (SQLite)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///javamastery.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Configure session settings
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Mail configuration for password reset and notifications
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT') or 587)
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', 'on', '1']
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

# Initialize mail extension
mail = Mail(app)

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(20), default='student')  # admin, instructor, student
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    progress = db.relationship('Progress', backref='user', lazy=True, cascade='all, delete-orphan')
    achievements = db.relationship('Achievement', backref='user', lazy=True, cascade='all, delete-orphan')
    enrollments = db.relationship('Enrollment', backref='user', lazy=True, cascade='all, delete-orphan')
    submissions = db.relationship('AssignmentSubmission', backref='student', lazy=True, cascade='all, delete-orphan')
    created_courses = db.relationship('Course', backref='instructor', lazy=True, foreign_keys='Course.instructor_id')

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.role}')"
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_instructor(self):
        return self.role == 'instructor'
    
    def is_student(self):
        return self.role == 'student'
    
    # 2FA fields
    totp_secret = db.Column(db.String(32))
    is_2fa_enabled = db.Column(db.Boolean, default=False)

class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    lesson_type = db.Column(db.String(20), default='text')  # text, video, audio, interactive
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    lesson_number = db.Column(db.Integer, nullable=False)
    multimedia_url = db.Column(db.String(200), nullable=True)  # URL for videos, images, etc.
    duration = db.Column(db.Integer, default=0)  # Duration in minutes
    status = db.Column(db.String(20), default='draft')  # draft, pending_approval, approved
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    progress = db.relationship('Progress', backref='lesson', lazy=True, cascade='all, delete-orphan')
    quizzes = db.relationship('Quiz', backref='lesson', lazy=True, cascade='all, delete-orphan')
    assignments = db.relationship('Assignment', backref='lesson', lazy=True, cascade='all, delete-orphan')
    notes = db.relationship('Note', backref='lesson', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"Lesson('{self.title}', '{self.lesson_type}', '{self.status}')"

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    level = db.Column(db.String(20), nullable=False)  # beginner, intermediate, advanced
    category = db.Column(db.String(50), default='General')  # Java, Python, etc.
    instructor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='draft')  # draft, pending_approval, approved, archived
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    lessons = db.relationship('Lesson', backref='course', lazy=True, cascade='all, delete-orphan')
    progress = db.relationship('Progress', backref='course', lazy=True, cascade='all, delete-orphan')
    enrollments = db.relationship('Enrollment', backref='course', lazy=True, cascade='all, delete-orphan')
    assignments = db.relationship('Assignment', backref='course', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"Course('{self.title}', '{self.level}', '{self.status}')"

class Progress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    score = db.Column(db.Float)
    time_spent = db.Column(db.Integer, default=0)  # Time spent in seconds
    date_completed = db.Column(db.DateTime)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_accessed = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    badge_icon = db.Column(db.String(50))  # Icon name for the achievement
    date_earned = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Achievement('{self.name}', '{self.user_id}')"

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    options = db.Column(db.JSON, nullable=False) # Stores options as JSON
    correct_answer = db.Column(db.String(1), nullable=False)  # A, B, C, or D
    points = db.Column(db.Integer, default=1)  # Points for correct answer
    time_limit = db.Column(db.Integer, default=0)  # Time limit in seconds, 0 = no limit
    status = db.Column(db.String(20), default='active')  # active, inactive
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Quiz('{self.title}', '{self.points} points')"

class QuizSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    selected_answer = db.Column(db.String(1))  # A, B, C, or D
    is_correct = db.Column(db.Boolean, default=False)
    score = db.Column(db.Float, default=0.0)  # Points earned
    time_taken = db.Column(db.Integer, default=0)  # Time taken in seconds
    date_submitted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"QuizSubmission(quiz_id={self.quiz_id}, user_id={self.user_id}, score={self.score})"

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    assignment_type = db.Column(db.String(20), default='coding')  # coding, text, file_upload
    due_date = db.Column(db.DateTime)
    max_score = db.Column(db.Integer, default=100)
    status = db.Column(db.String(20), default='active')  # active, inactive, closed
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationship
    submissions = db.relationship('AssignmentSubmission', backref='assignment', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"Assignment('{self.title}', '{self.assignment_type}', '{self.max_score} max points')"

class AssignmentSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False)
    submission_text = db.Column(db.Text)
    submission_file = db.Column(db.String(200))
    submission_code = db.Column(db.Text)
    score = db.Column(db.Float)
    feedback = db.Column(db.Text)
    status = db.Column(db.String(20), default='submitted')  # submitted, graded, pending
    date_submitted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_graded = db.Column(db.DateTime)

    def __repr__(self):
        return f"AssignmentSubmission(user_id={self.user_id}, assignment_id={self.assignment_id})"

# Forms for Admin to Add/Edit Content
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
    course_id = StringField('Course ID', validators=[DataRequired()]) # This will be a select field in the template
    lesson_number = StringField('Lesson Number', validators=[DataRequired()])
    multimedia_url = StringField('Multimedia URL')
    duration = StringField('Duration (minutes)')
    submit = SubmitField('Add Lesson')

class QuizForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=5, max=200)])
    lesson_id = StringField('Lesson ID', validators=[DataRequired()]) # Select field in template
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
    course_id = StringField('Course ID', validators=[DataRequired()]) # Select field in template
    lesson_id = StringField('Lesson ID', validators=[DataRequired()]) # Select field in template
    assignment_type = StringField('Assignment Type', validators=[DataRequired()])
    due_date = StringField('Due Date (YYYY-MM-DD HH:MM:SS)')
    max_score = StringField('Max Score')
    submit = SubmitField('Add Assignment')

class NoteForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=5, max=100)])
    content = TextAreaField('Content', validators=[DataRequired()])
    lesson_id = StringField('Lesson ID', validators=[DataRequired()]) # Select field in template
    submit = SubmitField('Add Note')

# Utility functions for security
def generate_token():
    """Generate a secure random token for password reset and other purposes"""
    return secrets.token_urlsafe(32)

def validate_password_strength(password):
    """Validate password strength requirements"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is strong"

def send_reset_email(user):
    """Send password reset email to user"""
    token = generate_token()
    expires_at = datetime.utcnow() + timedelta(hours=1)  # Token expires in 1 hour
    
    # Create password reset token record
    reset_token = PasswordResetToken(
        user_id=user.id,
        token=token,
        expires_at=expires_at
    )
    db.session.add(reset_token)
    db.session.commit()
    
    # Create and send email
    msg = Message(
        subject='Password Reset Request',
        recipients=[user.email],
        body=f'''To reset your password, visit the following link:
{url_for('reset_password', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    )
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def verify_reset_token(token):
    """Verify the password reset token"""
    reset_token = PasswordResetToken.query.filter_by(token=token).first()
    
    if not reset_token or reset_token.used or reset_token.expires_at < datetime.utcnow():
        return None
    
    return reset_token.user


# New model for lesson notes
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f"Note('{self.title}', lesson_id={self.lesson_id})"

# New model for course enrollment
class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    enrollment_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    completion_date = db.Column(db.DateTime)
    final_grade = db.Column(db.Float)  # Final grade for the course
    status = db.Column(db.String(20), default='enrolled')  # enrolled, completed, dropped

    def __repr__(self):
        return f"Enrollment(user_id={self.user_id}, course_id={self.course_id}, status='{self.status}')"

# New model for gradebook
class Grade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=True)
    grade = db.Column(db.Float, nullable=False)
    max_grade = db.Column(db.Float, default=100.0)
    date_recorded = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    grade_type = db.Column(db.String(20), default='assignment')  # assignment, quiz, exam, participation

    def __repr__(self):
        return f"Grade(user_id={self.user_id}, grade={self.grade}, type='{self.grade_type}')"

# New model for content categories
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Self-referential relationship for subcategories
    parent = db.relationship('Category', remote_side=[id], backref='subcategories')

    def __repr__(self):
        return f"Category('{self.name}')"

# New model for content approval workflow
class ContentApproval(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content_type = db.Column(db.String(20), nullable=False)  # course, lesson, assignment, quiz
    content_id = db.Column(db.Integer, nullable=False)  # ID of the content being approved
    submitted_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Approving admin/instructor
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    submission_notes = db.Column(db.Text)
    approval_notes = db.Column(db.Text)
    date_submitted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_approved = db.Column(db.DateTime)

    def __repr__(self):
        return f"ContentApproval(content_type='{self.content_type}', content_id={self.content_id}, status='{self.status}')"

# New model for user sessions (for enhanced security)
class UserSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_token = db.Column(db.String(10), unique=True, nullable=False)
    ip_address = db.Column(db.String(45))  # IPv4 or IPv6 address
    user_agent = db.Column(db.String(200))  # Browser information
    login_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    expires_at = db.Column(db.DateTime)

    def __repr__(self):
        return f"UserSession(user_id={self.user_id}, active={self.is_active})"

# New model for password reset tokens
class PasswordResetToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(10), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"PasswordResetToken(user_id={self.user_id}, used={self.used})"

# New model for user notifications
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(20), default='info') # info, warning, success, error
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Notification(user_id={self.user_id}, type='{self.notification_type}', read={self.is_read})"

# Forum models
class ForumCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"ForumCategory('{self.name}')"

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
    
    # Relationships
    user = db.relationship('User', backref='forum_threads')
    category = db.relationship('ForumCategory', backref='threads')
    replies = db.relationship('ForumReply', backref='thread', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"ForumThread('{self.title}')"

class ForumReply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    thread_id = db.Column(db.Integer, db.ForeignKey('forum_thread.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='forum_replies')

    def __repr__(self):
        return f"ForumReply(thread_id={self.thread_id}, user_id={self.user_id})"

# Multi-factor authentication setup
def generate_totp_secret():
    """Generate a secret for TOTP-based 2FA"""
    import pyotp
    return pyotp.random_base32()

def verify_totp_token(secret, token):
    """Verify a TOTP token"""
    import pyotp
    totp = pyotp.TOTP(secret)
    return totp.verify(token)

@app.route('/enable_2fa', methods=['POST'])
@login_required
def enable_2fa():
    """Enable 2FA for the current user"""
    if current_user.totp_secret:
        return jsonify({'success': False, 'message': '2FA is already enabled'})
    
    secret = generate_totp_secret()
    current_user.totp_secret = secret
    db.session.commit()
    
    # Generate QR code for authenticator apps
    import pyotp
    import qrcode
    from io import BytesIO
    import base64
    
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=current_user.email,
        issuer_name="Java Mastery LMS"
    )
    
    qr = qrcode.make(totp_uri)
    buffer = BytesIO()
    qr.save(buffer, format='PNG')
    qr_img = base64.b64encode(buffer.getvalue()).decode()
    
    return jsonify({
        'success': True,
        'qr_code': qr_img,
        'secret': secret,
        'uri': totp_uri
    })

@app.route('/verify_2fa', methods=['POST'])
@login_required
def verify_2fa():
    """Verify 2FA token and enable it"""
    data = request.get_json()
    token = data.get('token')
    
    if verify_totp_token(current_user.totp_secret, token):
        # 2FA is now fully enabled
        current_user.is_2fa_enabled = True
        db.session.commit()
        return jsonify({'success': True, 'message': '2FA enabled successfully'})
    else:
        return jsonify({'success': False, 'message': 'Invalid token'})

# Routes
@app.route('/')
def home():
    courses = Course.query.all()
    return render_template('index.html', courses=courses)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        # Validate input
        if not username or not email or not password:
            return jsonify({'success': False, 'message': 'All fields are required'})
        
        # Basic validation
        if len(username) < 3:
            return jsonify({'success': False, 'message': 'Username must be at least 3 characters'})
        
        if len(password) < 6:
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters'})
        
        # Check if user already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            return jsonify({'success': False, 'message': 'Username or email already exists'})
        
        # Hash the password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        # Create new user
        new_user = User(username=username, email=email, password_hash=hashed_password, role='student')
        db.session.add(new_user)
        db.session.commit()
        
        # Assign first achievement
        try:
            first_achievement = Achievement(
                user_id=new_user.id,
                name="First Steps",
                description="Completed registration"
            )
            db.session.add(first_achievement)
            db.session.commit()
        except Exception as e:
            print(f"Error adding achievement: {e}")
        
        return jsonify({'success': True, 'message': 'Registration successful! Redirecting to login...', 'redirect_url': '/login'})
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        two_factor_token = data.get('two_factor_token')  # For 2FA
        
        # Validate input
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password are required'})
        
        # Find user by username
        user = User.query.filter_by(username=username).first()
        
        # Check if user exists and password is correct
        if user and bcrypt.check_password_hash(user.password_hash, password):
            # Check if 2FA is enabled and token is provided
            if user.is_2fa_enabled:
                if not two_factor_token:
                    return jsonify({
                        'success': False,
                        'message': 'Two-factor authentication required',
                        'requires_2fa': True
                    })
                
                # Verify 2FA token
                if not user.totp_secret or not verify_totp_token(user.totp_secret, two_factor_token):
                    return jsonify({'success': False, 'message': 'Invalid 2FA token'})
            
            # Update last login time
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            login_user(user, remember=True)  # Set remember=True to maintain session
            session.permanent = True # Make session permanent based on config
            
            # Create user session record for enhanced security
            user_session = UserSession(
                user_id=user.id,
                session_token=secrets.token_urlsafe(32),
                ip_address=request.environ.get('REMOTE_ADDR'),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(user_session)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'redirect_url': url_for('dashboard')
            })
        else:
            return jsonify({'success': False, 'message': 'Invalid username or password'})
    
    return render_template('login.html')

@app.route('/test-login')
def test_login():
    """Test route to create a test account for debugging"""
    # Check if test user already exists
    test_user = User.query.filter_by(username='testuser').first()
    
    if not test_user:
        # Create test user
        hashed_password = bcrypt.generate_password_hash('password123').decode('utf-8')
        test_user = User(
            username='testuser',
            email='test@example.com',
            password_hash=hashed_password,
            role='student',
            is_verified=True
        )
        db.session.add(test_user)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Test user created', 'username': 'testuser', 'password': 'password123'})
    else:
        return jsonify({'success': True, 'message': 'Test user already exists', 'username': 'testuser', 'password': 'password123'})

@app.route('/logout')
@login_required
def logout():
    # Mark all sessions for this user as inactive
    user_sessions = UserSession.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).all()
    
    for user_session in user_sessions:
        user_session.is_active = False
    
    db.session.commit()
    
    logout_user()
    session.clear()  # Clear session data
    return redirect(url_for('home'))

# Role-based access control decorators
def instructor_required(f):
    """Decorator to require instructor or admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not (current_user.is_instructor() or current_user.is_admin()):
            return jsonify({'success': False, 'message': 'Instructor access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


def student_required(f):
    """Decorator to require student role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_student():
            return jsonify({'success': False, 'message': 'Student access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# Define the admin_required decorator
def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            return jsonify({'success': False, 'message': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# Password reset functionality
@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email', '').strip()
        
        if not email:
            return jsonify({'success': False, 'message': 'Email is required'})
        
        user = User.query.filter_by(email=email).first()
        if not user:
            # Don't reveal if email exists or not for security
            return jsonify({'success': True, 'message': 'If your email exists in our system, you will receive a password reset link'})
        
        # Send reset email
        if send_reset_email(user):
            return jsonify({'success': True, 'message': 'If your email exists in our system, you will receive a password reset link'})
        else:
            return jsonify({'success': False, 'message': 'Error sending reset email. Please try again later.'})
    
    return render_template('reset_password_request.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = verify_reset_token(token)
    if not user:
        return render_template('reset_password.html', error="Invalid or expired reset token")
    
    if request.method == 'POST':
        data = request.get_json()
        password = data.get('password', '')
        
        # Validate password strength
        is_strong, message = validate_password_strength(password)
        if not is_strong:
            return jsonify({'success': False, 'message': message})
        
        # Hash the new password
        user.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        
        # Mark token as used
        reset_token = PasswordResetToken.query.filter_by(token=token).first()
        if reset_token:
            reset_token.used = True
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Your password has been reset successfully'})
    
    return render_template('reset_password.html')

# Update the admin route with proper access control
@app.route('/admin')
@login_required
@admin_required
def admin():
    return render_template('admin.html')

# Enrollment management routes
@app.route('/api/enrollments', methods=['GET', 'POST'])
@login_required
def handle_enrollments():
    if request.method == 'POST':
        data = request.get_json()
        course_id = data.get('course_id')
        
        if not course_id:
            return jsonify({'success': False, 'message': 'Course ID is required'}), 400
        
        # Check if user is already enrolled
        existing_enrollment = Enrollment.query.filter_by(
            user_id=current_user.id,
            course_id=course_id
        ).first()
        
        if existing_enrollment:
            return jsonify({'success': False, 'message': 'Already enrolled in this course'}), 400
        
        # Check if course exists and is approved
        course = Course.query.get(course_id)
        if not course:
            return jsonify({'success': False, 'message': 'Course not found'}), 404
        
        if course.status != 'approved':
            return jsonify({'success': False, 'message': 'Course is not available for enrollment'}), 400
        
        # Create enrollment
        enrollment = Enrollment(
            user_id=current_user.id,
            course_id=course_id
        )
        db.session.add(enrollment)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Successfully enrolled in course'})
    
    # GET request - return user's enrollments
    user_enrollments = Enrollment.query.filter_by(user_id=current_user.id).all()
    enrollment_list = []
    for enrollment in user_enrollments:
        course = Course.query.get(enrollment.course_id)
        enrollment_list.append({
            'id': enrollment.id,
            'course_id': enrollment.course_id,
            'course_title': course.title if course else 'Unknown',
            'course_level': course.level if course else 'Unknown',
            'enrollment_date': enrollment.enrollment_date.isoformat(),
            'status': enrollment.status,
            'final_grade': enrollment.final_grade
        })
    
    return jsonify({'enrollments': enrollment_list})

@app.route('/api/enrollments/<int:course_id>', methods=['DELETE'])
@login_required
def drop_course(course_id):
    """Drop a course enrollment"""
    enrollment = Enrollment.query.filter_by(
        user_id=current_user.id,
        course_id=course_id
    ).first()
    
    if not enrollment:
        return jsonify({'success': False, 'message': 'Not enrolled in this course'}), 404
    
    # Update status to dropped
    enrollment.status = 'dropped'
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Successfully dropped course'})

# Enhanced progress tracking
@app.route('/api/progress/<int:lesson_id>', methods=['PUT'])
@login_required
def update_lesson_progress(lesson_id):
    """Update progress for a specific lesson"""
    data = request.get_json()
    completed = data.get('completed', False)
    score = data.get('score')
    time_spent = data.get('time_spent', 0)  # Time spent in seconds
    
    # Check if lesson exists
    lesson = Lesson.query.get_or_404(lesson_id)
    
    # Check if course is enrolled
    enrollment = Enrollment.query.filter_by(
        user_id=current_user.id,
        course_id=lesson.course_id
    ).first()
    
    if not enrollment:
        return jsonify({'success': False, 'message': 'Not enrolled in the course containing this lesson'}), 400
    
    # Check if progress record already exists
    progress_record = Progress.query.filter_by(
        user_id=current_user.id,
        lesson_id=lesson_id
    ).first()
    
    if progress_record:
        # Update existing record
        progress_record.completed = completed
        if score is not None:
            progress_record.score = score
        progress_record.time_spent = time_spent
        if completed:
            progress_record.date_completed = datetime.utcnow()
        progress_record.last_accessed = datetime.utcnow()
    else:
        # Create new record
        progress_record = Progress(
            user_id=current_user.id,
            lesson_id=lesson_id,
            course_id=lesson.course_id,
            completed=completed,
            score=score,
            time_spent=time_spent
        )
        if completed:
            progress_record.date_completed = datetime.utcnow()
        db.session.add(progress_record)
    
    db.session.commit()
    
    # Check for achievements
    check_and_assign_achievements(current_user.id)
    
    # Update enrollment status if all lessons are completed
    update_enrollment_status(lesson.course_id, current_user.id)
    
    return jsonify({'success': True, 'message': 'Progress updated successfully'})

def update_enrollment_status(course_id, user_id):
    """Update enrollment status based on course completion"""
    course = Course.query.get(course_id)
    if not course:
        return
    
    # Count total lessons in the course
    total_lessons = Lesson.query.filter_by(course_id=course_id).count()
    
    # Count completed lessons for this user
    completed_lessons = Progress.query.filter_by(
        user_id=user_id,
        course_id=course_id,
        completed=True
    ).count()
    
    # Get the enrollment record
    enrollment = Enrollment.query.filter_by(
        user_id=user_id,
        course_id=course_id
    ).first()
    
    if not enrollment:
        return
    
    # If all lessons are completed, mark enrollment as completed
    if completed_lessons == total_lessons and total_lessons > 0:
        enrollment.status = 'completed'
        enrollment.completion_date = datetime.utcnow()
        
        # Calculate final grade based on average of all lesson scores
        all_scores = Progress.query.filter_by(
            user_id=user_id,
            course_id=course_id
        ).with_entities(Progress.score).all()
        
        scores = [score[0] for score in all_scores if score[0] is not None]
        if scores:
            enrollment.final_grade = sum(scores) / len(scores)
        
        db.session.commit()
        
        # Create a notification for course completion
        completion_notification = Notification(
            user_id=user_id,
            title="Course Completed!",
            message=f"Congratulations! You have completed the course '{course.title}'.",
            notification_type="success"
        )
        db.session.add(completion_notification)
        db.session.commit()

# Quiz management
@app.route('/api/quizzes', methods=['GET', 'POST'])
@login_required
def quizzes_api():
    """Get all quizzes (GET) or create a new quiz (POST)"""
    if request.method == 'GET':
        quizzes = Quiz.query.all()
        quizzes_data = [{
            'id': q.id,
            'question': q.question,
            'lesson_title': q.lesson.title if q.lesson else 'Unknown',
            'status': 'approved',
            'date_created': q.date_created.isoformat() if hasattr(q, 'date_created') else ''
        } for q in quizzes]
        return jsonify({'quizzes': quizzes_data})
    
    # POST method - Create a new quiz
    if not (current_user.is_instructor() or current_user.is_admin()):
        return jsonify({'success': False, 'message': 'Instructor or admin access required'}), 403
    
    data = request.get_json()
    title = data.get('title')
    question = data.get('question')
    options = data.get('options')
    correct_answer = data.get('correct_answer')
    lesson_id = data.get('lesson_id')
    points = data.get('points', 1)
    time_limit = data.get('time_limit', 0)
    
    if not title or not question or not options or not correct_answer or not lesson_id:
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    # Validate lesson exists and user has permission
    lesson = Lesson.query.get(lesson_id)
    if not lesson:
        return jsonify({'success': False, 'message': 'Lesson not found'}), 404
    
    course = Course.query.get(lesson.course_id)
    if course.instructor_id != current_user.id and not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Insufficient permissions'}), 403
    
    # Validate options format
    if not isinstance(options, list) or len(options) < 2:
        return jsonify({'success': False, 'message': 'Options must be a list with at least 2 items'}), 400
    
    # Validate correct answer
    valid_answers = ['A', 'B', 'C', 'D']
    if correct_answer not in valid_answers[:len(options)]:
        return jsonify({'success': False, 'message': 'Correct answer must be one of the provided options'}), 400
    
    quiz = Quiz(
        title=title,
        question=question,
        options=options,
        correct_answer=correct_answer,
        lesson_id=lesson_id,
        points=points,
        time_limit=time_limit,
        status='pending_approval'  # New quizzes require approval
    )
    db.session.add(quiz)
    db.session.commit()
    
    # Create approval request for the new quiz
    approval_request = ContentApproval(
        content_type='quiz',
        content_id=quiz.id,
        submitted_by=current_user.id,
        submission_notes=f'New quiz "{title}" submitted for approval'
    )
    db.session.add(approval_request)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Quiz created successfully', 'quiz_id': quiz.id})

@app.route('/api/quizzes/<int:quiz_id>', methods=['PUT'])
@login_required
def update_quiz(quiz_id):
    """Update quiz information"""
    quiz = Quiz.query.get_or_404(quiz_id)
    lesson = Lesson.query.get(quiz.lesson_id)
    course = Course.query.get(lesson.course_id)
    
    # Check permissions
    if course.instructor_id != current_user.id and not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Insufficient permissions'}), 403
    
    data = request.get_json()
    
    # Update allowed fields
    if 'title' in data:
        quiz.title = data['title']
    if 'question' in data:
        quiz.question = data['question']
    if 'options' in data:
        quiz.options = data['options']
    if 'correct_answer' in data:
        quiz.correct_answer = data['correct_answer']
    if 'points' in data:
        quiz.points = data['points']
    if 'time_limit' in data:
        quiz.time_limit = data['time_limit']
    
    quiz.date_updated = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Quiz updated successfully'})

@app.route('/api/quizzes/<int:quiz_id>', methods=['DELETE'])
@login_required
def delete_quiz(quiz_id):
    """Delete a quiz"""
    quiz = Quiz.query.get_or_404(quiz_id)
    lesson = Lesson.query.get(quiz.lesson_id)
    course = Course.query.get(lesson.course_id)
    
    # Check permissions
    if course.instructor_id != current_user.id and not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Insufficient permissions'}), 403
    
    # Check if quiz has submissions - prevent deletion if students have taken it
    submissions_count = QuizSubmission.query.filter_by(quiz_id=quiz_id).count()
    if submissions_count > 0:
        return jsonify({'success': False, 'message': 'Cannot delete quiz with student submissions'}), 400
    
    db.session.delete(quiz)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Quiz deleted successfully'})

# Assignment management
@app.route('/api/assignments', methods=['GET', 'POST'])
@login_required
def assignments_api():
    """Get all assignments (GET) or create a new assignment (POST)"""
    if request.method == 'GET':
        assignments = Assignment.query.all()
        assignments_data = [{
            'id': a.id,
            'title': a.title,
            'course_title': a.course.title if a.course else 'Unknown',
            'assignment_type': a.assignment_type or 'homework',
            'status': 'approved',
            'date_created': a.date_created.isoformat() if hasattr(a, 'date_created') else ''
        } for a in assignments]
        return jsonify({'assignments': assignments_data})
    
    # POST method - Create a new assignment
    if not (current_user.is_instructor() or current_user.is_admin()):
        return jsonify({'success': False, 'message': 'Instructor or admin access required'}), 403
    
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    course_id = data.get('course_id')
    lesson_id = data.get('lesson_id')
    assignment_type = data.get('assignment_type', 'coding')
    due_date = data.get('due_date')
    max_score = data.get('max_score', 100)
    
    if not title or not description or not course_id or not lesson_id:
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    # Validate course and lesson exist and user has permission
    course = Course.query.get(course_id)
    lesson = Lesson.query.get(lesson_id)
    
    if not course or not lesson:
        return jsonify({'success': False, 'message': 'Course or lesson not found'}), 404
    
    if course.instructor_id != current_user.id and not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Insufficient permissions'}), 403
    
    # Convert due_date string to datetime if provided
    due_date_obj = None
    if due_date:
        try:
            due_date_obj = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid date format'}), 400
    
    assignment = Assignment(
        title=title,
        description=description,
        course_id=course_id,
        lesson_id=lesson_id,
        assignment_type=assignment_type,
        due_date=due_date_obj,
        max_score=max_score,
        status='pending_approval'  # New assignments require approval
    )
    db.session.add(assignment)
    db.session.commit()
    
    # Create approval request for the new assignment
    approval_request = ContentApproval(
        content_type='assignment',
        content_id=assignment.id,
        submitted_by=current_user.id,
        submission_notes=f'New assignment "{title}" submitted for approval'
    )
    db.session.add(approval_request)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Assignment created successfully', 'assignment_id': assignment.id})

@app.route('/api/assignments/<int:assignment_id>', methods=['PUT'])
@login_required
def update_assignment(assignment_id):
    """Update assignment information"""
    assignment = Assignment.query.get_or_404(assignment_id)
    course = Course.query.get(assignment.course_id)
    
    # Check permissions
    if course.instructor_id != current_user.id and not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Insufficient permissions'}), 403
    
    data = request.get_json()
    
    # Update allowed fields
    if 'title' in data:
        assignment.title = data['title']
    if 'description' in data:
        assignment.description = data['description']
    if 'assignment_type' in data:
        assignment.assignment_type = data['assignment_type']
    if 'due_date' in data:
        try:
            assignment.due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid date format'}), 400
    if 'max_score' in data:
        assignment.max_score = data['max_score']
    
    assignment.date_updated = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Assignment updated successfully'})

@app.route('/api/assignments/<int:assignment_id>', methods=['DELETE'])
@login_required
def delete_assignment(assignment_id):
    """Delete an assignment"""
    assignment = Assignment.query.get_or_404(assignment_id)
    course = Course.query.get(assignment.course_id)
    
    # Check permissions
    if course.instructor_id != current_user.id and not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Insufficient permissions'}), 403
    
    # Check if assignment has submissions - prevent deletion if students have submitted
    submissions_count = AssignmentSubmission.query.filter_by(assignment_id=assignment_id).count()
    if submissions_count > 0:
        return jsonify({'success': False, 'message': 'Cannot delete assignment with student submissions'}), 400
    
    db.session.delete(assignment)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Assignment deleted successfully'})

# Gradebook functionality
@app.route('/api/grades', methods=['GET', 'POST'])
@login_required
def handle_grades():
    if request.method == 'POST':
        data = request.get_json()
        user_id = data.get('user_id')  # Only instructors/admins can grade others
        assignment_id = data.get('assignment_id')
        quiz_id = data.get('quiz_id')
        grade = data.get('grade')
        max_grade = data.get('max_grade', 100)
        
        # Check permissions
        if current_user.id != user_id and not (current_user.is_instructor() or current_user.is_admin()):
            return jsonify({'success': False, 'message': 'Insufficient permissions'}), 403
        
        if grade is None or grade < 0:
            return jsonify({'success': False, 'message': 'Invalid grade value'}), 400
        
        # Determine grade type and verify content exists
        grade_type = 'assignment' if assignment_id else 'quiz'
        if assignment_id:
            assignment = Assignment.query.get(assignment_id)
            if not assignment:
                return jsonify({'success': False, 'message': 'Assignment not found'}), 404
            # Check permission to grade assignment
            if not current_user.is_admin() and assignment.course.instructor_id != current_user.id:
                return jsonify({'success': False, 'message': 'Insufficient permissions'}), 403
        elif quiz_id:
            quiz = Quiz.query.get(quiz_id)
            if not quiz:
                return jsonify({'success': False, 'message': 'Quiz not found'}), 404
            # Check permission to grade quiz
            if not current_user.is_admin() and quiz.lesson.course.instructor_id != current_user.id:
                return jsonify({'success': False, 'message': 'Insufficient permissions'}), 403
        else:
            return jsonify({'success': False, 'message': 'Either assignment_id or quiz_id must be provided'}), 400
        
        # Create or update grade
        grade_record = Grade(
            user_id=user_id,
            assignment_id=assignment_id,
            quiz_id=quiz_id,
            grade=grade,
            max_grade=max_grade,
            grade_type=grade_type
        )
        db.session.add(grade_record)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Grade recorded successfully'})
    
    # GET request - return grades for current user or all grades if instructor/admin
    if current_user.is_instructor() or current_user.is_admin():
        # Return all grades for courses this instructor teaches
        grades = Grade.query.join(User).join(Course,
            (Grade.assignment.has(assignment.course_id == Course.id)) |
            (Grade.quiz.has(Quiz.lesson.has(Lesson.course_id == Course.id)))
        ).filter(Course.instructor_id == current_user.id).all()
    else:
        # Return grades for current user only
        grades = Grade.query.filter_by(user_id=current_user.id).all()
    
    grade_list = []
    for grade in grades:
        grade_data = {
            'id': grade.id,
            'user_id': grade.user_id,
            'grade': grade.grade,
            'max_grade': grade.max_grade,
            'grade_type': grade.grade_type,
            'date_recorded': grade.date_recorded.isoformat()
        }
        
        if grade.assignment_id:
            assignment = Assignment.query.get(grade.assignment_id)
            grade_data['assignment_title'] = assignment.title if assignment else 'Unknown'
        elif grade.quiz_id:
            quiz = Quiz.query.get(grade.quiz_id)
            grade_data['quiz_title'] = quiz.title if quiz else 'Unknown'
        
        grade_list.append(grade_data)
    
    return jsonify({'grades': grade_list})

@app.route('/api/grades/<int:user_id>/course/<int:course_id>')
@login_required
def get_user_course_grades(user_id, course_id):
    """Get all grades for a user in a specific course"""
    # Check permissions
    if current_user.id != user_id and not (current_user.is_instructor() or current_user.is_admin()):
        return jsonify({'success': False, 'message': 'Insufficient permissions'}), 403
    
    # Get all assignments and quizzes for this course
    course_assignments = Assignment.query.filter_by(course_id=course_id).all()
    course_lessons = Lesson.query.filter_by(course_id=course_id).all()
    course_quizzes = []
    for lesson in course_lessons:
        lesson_quizzes = Quiz.query.filter_by(lesson_id=lesson.id).all()
        course_quizzes.extend(lesson_quizzes)
    
    # Get grades for this user in this course
    grades = Grade.query.filter_by(user_id=user_id).all()
    
    # Organize grades by type
    assignment_grades = [g for g in grades if g.assignment_id in [a.id for a in course_assignments]]
    quiz_grades = [g for g in grades if g.quiz_id in [q.id for q in course_quizzes]]
    
    # Calculate averages
    total_assignment_score = sum(g.grade for g in assignment_grades) if assignment_grades else 0
    total_quiz_score = sum(g.grade for g in quiz_grades) if quiz_grades else 0
    
    avg_assignment_grade = total_assignment_score / len(assignment_grades) if assignment_grades else 0
    avg_quiz_grade = total_quiz_score / len(quiz_grades) if quiz_grades else 0
    
    return jsonify({
        'course_id': course_id,
        'user_id': user_id,
        'assignment_grades': [{
            'assignment_id': g.assignment_id,
            'grade': g.grade,
            'max_grade': g.max_grade,
            'assignment_title': Assignment.query.get(g.assignment_id).title if g.assignment_id else 'Unknown'
        } for g in assignment_grades],
        'quiz_grades': [{
            'quiz_id': g.quiz_id,
            'grade': g.grade,
            'max_grade': g.max_grade,
            'quiz_title': Quiz.query.get(g.quiz_id).title if g.quiz_id else 'Unknown'
        } for g in quiz_grades],
        'average_assignment_grade': avg_assignment_grade,
        'average_quiz_grade': avg_quiz_grade
    })

# Content approval workflow
@app.route('/api/content_approval', methods=['GET', 'POST'])
@login_required
def content_approval():
    if request.method == 'POST':
        data = request.get_json()
        content_type = data.get('content_type')
        content_id = data.get('content_id')
        submission_notes = data.get('submission_notes', '')
        
        # Validate content type
        valid_content_types = ['course', 'lesson', 'assignment', 'quiz']
        if content_type not in valid_content_types:
            return jsonify({'success': False, 'message': 'Invalid content type'}), 400
        
        # Check if content exists
        content_exists = False
        if content_type == 'course':
            content_exists = Course.query.get(content_id) is not None
        elif content_type == 'lesson':
            content_exists = Lesson.query.get(content_id) is not None
        elif content_type == 'assignment':
            content_exists = Assignment.query.get(content_id) is not None
        elif content_type == 'quiz':
            content_exists = Quiz.query.get(content_id) is not None
        
        if not content_exists:
            return jsonify({'success': False, 'message': 'Content not found'}), 404
        
        # Check if user has permission to submit for approval
        # For courses, only instructors can submit
        if content_type == 'course':
            course = Course.query.get(content_id)
            if course.instructor_id != current_user.id and not current_user.is_admin():
                return jsonify({'success': False, 'message': 'Insufficient permissions'}), 403
        
        # Check if there's already a pending approval request for this content
        existing_request = ContentApproval.query.filter_by(
            content_type=content_type,
            content_id=content_id,
            status='pending'
        ).first()
        
        if existing_request:
            return jsonify({'success': False, 'message': 'Approval request already exists'}), 400
        
        # Create approval request
        approval_request = ContentApproval(
            content_type=content_type,
            content_id=content_id,
            submitted_by=current_user.id,
            submission_notes=submission_notes
        )
        db.session.add(approval_request)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Content submitted for approval'})
    
    # GET request - return approval requests based on user role
    if current_user.is_admin():
        # Admins can see all requests
        approval_requests = ContentApproval.query.all()
    elif current_user.is_instructor():
        # Instructors can see requests for content they created
        approval_requests = ContentApproval.query.filter(
            ContentApproval.submitted_by == current_user.id
        ).all()
    else:
        # Students can only see their own requests
        approval_requests = ContentApproval.query.filter_by(
            submitted_by=current_user.id
        ).all()
    
    request_list = []
    for req in approval_requests:
        # Get content details
        content_title = "Unknown"
        if req.content_type == 'course':
            course = Course.query.get(req.content_id)
            content_title = course.title if course else "Unknown Course"
        elif req.content_type == 'lesson':
            lesson = Lesson.query.get(req.content_id)
            content_title = lesson.title if lesson else "Unknown Lesson"
        elif req.content_type == 'assignment':
            assignment = Assignment.query.get(req.content_id)
            content_title = assignment.title if assignment else "Unknown Assignment"
        elif req.content_type == 'quiz':
            quiz = Quiz.query.get(req.content_id)
            content_title = quiz.title if quiz else "Unknown Quiz"
        
        # Get user who submitted
        submitter = User.query.get(req.submitted_by)
        
        request_data = {
            'id': req.id,
            'content_type': req.content_type,
            'content_id': req.content_id,
            'content_title': content_title,
            'submitted_by': req.submitted_by,
            'submitter_name': submitter.username if submitter else 'Unknown',
            'status': req.status,
            'submission_notes': req.submission_notes,
            'approval_notes': req.approval_notes,
            'date_submitted': req.date_submitted.isoformat(),
            'date_approved': req.date_approved.isoformat() if req.date_approved else None
        }
        request_list.append(request_data)
    
    return jsonify({'approval_requests': request_list})

@app.route('/api/content_approval/<int:request_id>', methods=['PUT'])
@login_required
@admin_required
def approve_content(request_id):
    """Approve or reject content"""
    data = request.get_json()
    action = data.get('action')  # 'approve' or 'reject'
    approval_notes = data.get('approval_notes', '')
    
    if action not in ['approve', 'reject']:
        return jsonify({'success': False, 'message': 'Invalid action'}), 400
    
    approval_request = ContentApproval.query.get_or_404(request_id)
    
    # Update approval request
    approval_request.status = 'approved' if action == 'approve' else 'rejected'
    approval_request.approved_by = current_user.id
    approval_request.approval_notes = approval_notes
    approval_request.date_approved = datetime.utcnow()
    
    # If approved, update content status
    if action == 'approve':
        if approval_request.content_type == 'course':
            content = Course.query.get(approval_request.content_id)
            if content:
                content.status = 'approved'
        elif approval_request.content_type == 'lesson':
            content = Lesson.query.get(approval_request.content_id)
            if content:
                content.status = 'approved'
        elif approval_request.content_type == 'assignment':
            content = Assignment.query.get(approval_request.content_id)
            if content:
                content.status = 'active'
        elif approval_request.content_type == 'quiz':
            content = Quiz.query.get(approval_request.content_id)
            if content:
                content.status = 'active'
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'Content {action}ed successfully'})

# Search functionality
@app.route('/api/search')
@login_required
def search_content():
    """Search across courses, lessons, assignments, and quizzes"""
    query = request.args.get('q', '').strip()
    content_type = request.args.get('type', 'all')  # all, course, lesson, assignment, quiz
    
    if not query:
        return jsonify({'results': []})
    
    results = []
    
    # Search courses
    if content_type in ['all', 'course']:
        courses = Course.query.filter(
            Course.title.contains(query) | Course.description.contains(query)
        ).all()
        for course in courses:
            results.append({
                'type': 'course',
                'id': course.id,
                'title': course.title,
                'description': course.description[:100] + '...' if len(course.description) > 100 else course.description,
                'url': url_for('course_detail', course_id=course.id)
            })
    
    # Search lessons
    if content_type in ['all', 'lesson']:
        lessons = Lesson.query.filter(
            Lesson.title.contains(query) | Lesson.content.contains(query)
        ).all()
        for lesson in lessons:
            results.append({
                'type': 'lesson',
                'id': lesson.id,
                'title': lesson.title,
                'course_id': lesson.course_id,
                'course_title': Course.query.get(lesson.course_id).title if lesson.course_id else 'Unknown',
                'url': url_for('lesson_detail', lesson_id=lesson.id)
            })
    
    # Search assignments
    if content_type in ['all', 'assignment']:
        assignments = Assignment.query.filter(
            Assignment.title.contains(query) | Assignment.description.contains(query)
        ).all()
        for assignment in assignments:
            results.append({
                'type': 'assignment',
                'id': assignment.id,
                'title': assignment.title,
                'course_id': assignment.course_id,
                'course_title': Course.query.get(assignment.course_id).title if assignment.course_id else 'Unknown',
                'url': url_for('assignment_detail', assignment_id=assignment.id)
            })
    
    # Search quizzes
    if content_type in ['all', 'quiz']:
        quizzes = Quiz.query.filter(
            Quiz.title.contains(query) | Quiz.question.contains(query)
        ).all()
        for quiz in quizzes:
            results.append({
                'type': 'quiz',
                'id': quiz.id,
                'title': quiz.title,
                'question': quiz.question[:100] + '...' if len(quiz.question) > 100 else quiz.question,
                'lesson_id': quiz.lesson_id,
                'url': url_for('quiz_detail', quiz_id=quiz.id)
            })
    
    return jsonify({'results': results})

# Content categorization
@app.route('/api/users', methods=['GET'])
@login_required
@admin_required
def get_users():
    """Get all users"""
    users = User.query.all()
    users_data = [{
        'id': u.id,
        'username': u.username,
        'email': u.email,
        'role': u.role,
        'date_created': u.date_created.isoformat() if u.date_created else ''
    } for u in users]
    return jsonify({'users': users_data})

@app.route('/api/categories', methods=['GET', 'POST'])
@login_required
@admin_required
def handle_categories():
    if request.method == 'POST':
        data = request.get_json()
        name = data.get('name')
        description = data.get('description', '')
        parent_id = data.get('parent_id')
        
        if not name:
            return jsonify({'success': False, 'message': 'Category name is required'}), 400
        
        # Check if category already exists
        existing_category = Category.query.filter_by(name=name).first()
        if existing_category:
            return jsonify({'success': False, 'message': 'Category already exists'}), 400
        
        category = Category(
            name=name,
            description=description,
            parent_id=parent_id
        )
        db.session.add(category)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Category created successfully'})
    
    # GET request - return all categories
    categories = Category.query.all()
    category_list = []
    for category in categories:
        parent_name = None
        if category.parent_id:
            parent = Category.query.get(category.parent_id)
            parent_name = parent.name if parent else None
        
        category_list.append({
            'id': category.id,
            'name': category.name,
            'description': category.description,
            'parent_id': category.parent_id,
            'parent_name': parent_name,
            'date_created': category.date_created.isoformat()
        })
    
    return jsonify({'categories': category_list})

@app.route('/api/courses/<int:course_id>/category', methods=['PUT'])
@login_required
@admin_required
def assign_course_category(course_id):
    """Assign a category to a course"""
    data = request.get_json()
    category_id = data.get('category_id')
    
    course = Course.query.get_or_404(course_id)
    category = Category.query.get_or_404(category_id)
    
    course.category = category.name
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Category assigned successfully'})

# Enhanced course creation with instructor assignment
@app.route('/api/courses', methods=['GET', 'POST'])
@login_required
def courses_api():
    """Get all courses (GET) or create a new course (POST)"""
    if request.method == 'GET':
        courses = Course.query.all()
        courses_data = [{
            'id': c.id,
            'title': c.title,
            'level': c.level,
            'instructor_name': c.instructor.username if c.instructor else 'Unknown',
            'status': c.status,
            'lesson_count': len(c.lessons),
            'date_created': c.date_created.isoformat()
        } for c in courses]
        return jsonify({'courses': courses_data})
    
    # POST method - Create a new course (instructors can create their own courses)
    if not (current_user.is_instructor() or current_user.is_admin()):
        return jsonify({'success': False, 'message': 'Instructor or admin access required'}), 403
    
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    level = data.get('level')
    category = data.get('category', 'General')
    if not title or not description or not level:
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    # Create course with current user as instructor
    course = Course(
        title=title,
        description=description,
        level=level,
        category=category,
        instructor_id=current_user.id,
        status='pending_approval' # New courses require approval
    )
    db.session.add(course)
    db.session.commit()
    
    # Create approval request for the new course
    approval_request = ContentApproval(
        content_type='course',
        content_id=course.id,
        submitted_by=current_user.id,
        submission_notes=f'New course "{title}" submitted for approval'
    )
    db.session.add(approval_request)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Course created successfully', 'course_id': course.id})

# Course organization and management
@app.route('/api/courses/<int:course_id>', methods=['PUT'])
@login_required
def update_course(course_id):
    """Update course information"""
    course = Course.query.get_or_404(course_id)
    
    # Check permissions - only instructor who created the course or admin can update
    if course.instructor_id != current_user.id and not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Insufficient permissions'}), 403
    
    data = request.get_json()
    
    # Update allowed fields
    if 'title' in data:
        course.title = data['title']
    if 'description' in data:
        course.description = data['description']
    if 'level' in data:
        course.level = data['level']
    if 'category' in data:
        course.category = data['category']
    
    course.date_updated = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Course updated successfully'})

@app.route('/api/courses/<int:course_id>', methods=['DELETE'])
@login_required
def delete_course(course_id):
    """Delete a course"""
    course = Course.query.get_or_404(course_id)
    
    # Check permissions - only instructor who created the course or admin can delete
    if course.instructor_id != current_user.id and not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Insufficient permissions'}), 403
    
    # Check if course has enrollments - prevent deletion if students are enrolled
    enrollments = Enrollment.query.filter_by(course_id=course_id).count()
    if enrollments > 0:
        return jsonify({'success': False, 'message': 'Cannot delete course with active enrollments'}), 400
    
    db.session.delete(course)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Course deleted successfully'})

# Lesson management
@app.route('/api/lessons', methods=['GET', 'POST'])
@login_required
def lessons_api():
    """Get all lessons (GET) or create a new lesson (POST)"""
    if request.method == 'GET':
        lessons = Lesson.query.all()
        lessons_data = [{
            'id': l.id,
            'title': l.title,
            'course_title': l.course.title if l.course else 'Unknown',
            'lesson_type': l.lesson_type,
            'status': l.status,
            'date_created': l.date_created.isoformat()
        } for l in lessons]
        return jsonify({'lessons': lessons_data})
    
    # POST method - Create a new lesson
    if not (current_user.is_instructor() or current_user.is_admin()):
        return jsonify({'success': False, 'message': 'Instructor or admin access required'}), 403
    
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')
    course_id = data.get('course_id')
    lesson_number = data.get('lesson_number')
    lesson_type = data.get('lesson_type', 'text')
    multimedia_url = data.get('multimedia_url')
    duration = data.get('duration', 0)
    
    if not title or not content or not course_id or not lesson_number:
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    # Verify course exists and user has permission to add lessons
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'success': False, 'message': 'Course not found'}), 404
    
    if course.instructor_id != current_user.id and not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Insufficient permissions'}), 403
    
    lesson = Lesson(
        title=title,
        content=content,
        lesson_type=lesson_type,
        course_id=course_id,
        lesson_number=lesson_number,
        multimedia_url=multimedia_url,
        duration=duration,
        status='pending_approval'  # New lessons require approval
    )
    db.session.add(lesson)
    db.session.commit()
    
    # Create approval request for the new lesson
    approval_request = ContentApproval(
        content_type='lesson',
        content_id=lesson.id,
        submitted_by=current_user.id,
        submission_notes=f'New lesson "{title}" submitted for approval'
    )
    db.session.add(approval_request)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Lesson created successfully', 'lesson_id': lesson.id})

@app.route('/api/lessons/<int:lesson_id>', methods=['PUT'])
@login_required
def update_lesson(lesson_id):
    """Update lesson information"""
    lesson = Lesson.query.get_or_404(lesson_id)
    course = Course.query.get(lesson.course_id)
    
    # Check permissions
    if course.instructor_id != current_user.id and not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Insufficient permissions'}), 403
    
    data = request.get_json()
    
    # Update allowed fields
    if 'title' in data:
        lesson.title = data['title']
    if 'content' in data:
        lesson.content = data['content']
    if 'lesson_type' in data:
        lesson.lesson_type = data['lesson_type']
    if 'multimedia_url' in data:
        lesson.multimedia_url = data['multimedia_url']
    if 'duration' in data:
        lesson.duration = data['duration']
    
    lesson.date_updated = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Lesson updated successfully'})

@app.route('/api/lessons/<int:lesson_id>', methods=['DELETE'])
@login_required
def delete_lesson(lesson_id):
    """Delete a lesson"""
    lesson = Lesson.query.get_or_404(lesson_id)
    course = Course.query.get(lesson.course_id)
    
    # Check permissions
    if course.instructor_id != current_user.id and not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Insufficient permissions'}), 403
    
    # Check if lesson has progress records - prevent deletion if students have started
    progress_count = Progress.query.filter_by(lesson_id=lesson_id).count()
    if progress_count > 0:
        return jsonify({'success': False, 'message': 'Cannot delete lesson with student progress'}), 400
    
    db.session.delete(lesson)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Lesson deleted successfully'})

# Note management
@app.route('/api/notes', methods=['POST'])
@login_required
def create_note():
    """Create a new note"""
    if not (current_user.is_instructor() or current_user.is_admin()):
        return jsonify({'success': False, 'message': 'Instructor or admin access required'}), 403
    
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')
    lesson_id = data.get('lesson_id')
    
    if not title or not content or not lesson_id:
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    # Verify lesson exists and user has permission
    lesson = Lesson.query.get(lesson_id)
    if not lesson:
        return jsonify({'success': False, 'message': 'Lesson not found'}), 404
    
    course = Course.query.get(lesson.course_id)
    if course.instructor_id != current_user.id and not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Insufficient permissions'}), 403
    
    note = Note(
        title=title,
        content=content,
        lesson_id=lesson_id
    )
    db.session.add(note)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Note created successfully', 'note_id': note.id})

@app.route('/api/notes/<int:note_id>', methods=['PUT'])
@login_required
def update_note(note_id):
    """Update note information"""
    note = Note.query.get_or_404(note_id)
    lesson = Lesson.query.get(note.lesson_id)
    course = Course.query.get(lesson.course_id)
    
    # Check permissions
    if course.instructor_id != current_user.id and not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Insufficient permissions'}), 403
    
    data = request.get_json()
    
    # Update allowed fields
    if 'title' in data:
        note.title = data['title']
    if 'content' in data:
        note.content = data['content']
    
    note.date_updated = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Note updated successfully'})

@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
@login_required
def delete_note(note_id):
    """Delete a note"""
    note = Note.query.get_or_404(note_id)
    lesson = Lesson.query.get(note.lesson_id)
    course = Course.query.get(lesson.course_id)
    
    # Check permissions
    if course.instructor_id != current_user.id and not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Insufficient permissions'}), 403
    
    db.session.delete(note)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Note deleted successfully'})

@app.route('/api/notes/lesson/<int:lesson_id>')
@login_required
def get_notes_by_lesson(lesson_id):
    """Get all notes for a specific lesson"""
    lesson = Lesson.query.get_or_404(lesson_id)
    
    # Check if user is enrolled in the course or is an instructor/admin
    if not (current_user.is_admin() or current_user.is_instructor() or
            Enrollment.query.filter_by(user_id=current_user.id, course_id=lesson.course_id).first()):
        return jsonify({'success': False, 'message': 'Insufficient permissions'}), 403
    
    notes = Note.query.filter_by(lesson_id=lesson_id).all()
    
    notes_list = []
    for note in notes:
        notes_list.append({
            'id': note.id,
            'title': note.title,
            'content': note.content,
            'lesson_id': note.lesson_id,
            'date_created': note.date_created.isoformat(),
            'date_updated': note.date_updated.isoformat()
        })
    
    return jsonify({'notes': notes_list})


@app.route('/profile')
@login_required
def profile():
    # Get user's progress
    user_progress = Progress.query.filter_by(user_id=current_user.id).all()
    user_achievements = Achievement.query.filter_by(user_id=current_user.id).all()
    
    return render_template('profile.html',
                          progress=user_progress,
                          achievements=user_achievements)

@app.route('/dashboard')
@login_required
def dashboard():
    # Get all courses
    courses = Course.query.all()
    
    # Calculate progress for each course
    for course in courses:
        total_lessons = Lesson.query.filter_by(course_id=course.id).count()
        completed_lessons = Progress.query.filter_by(
            user_id=current_user.id,
            course_id=course.id,
            completed=True
        ).count()
        
        course.total_lessons = total_lessons
        course.completed_lessons = completed_lessons
        course.progress_percentage = (completed_lessons / total_lessons * 10) if total_lessons > 0 else 0
    
    return render_template('dashboard.html', courses=courses)

@app.route('/forum')
@login_required
def forum():
    return render_template('forum.html')

@app.route('/api/lessons/<int:lesson_id>')
@login_required
def get_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    return jsonify({
        'id': lesson.id,
        'title': lesson.title,
        'content': lesson.content,
        'course_id': lesson.course_id
    })

@app.route('/api/progress', methods=['GET', 'POST'])
@login_required
def handle_progress():
    if request.method == 'POST':
        data = request.get_json()
        lesson_id = data.get('lesson_id')
        course_id = data.get('course_id')
        completed = data.get('completed', False)
        score = data.get('score')
        
        # Check if progress record already exists
        progress_record = Progress.query.filter_by(
            user_id=current_user.id,
            lesson_id=lesson_id
        ).first()
        
        if progress_record:
            # Update existing record
            progress_record.completed = completed
            if score is not None:
                progress_record.score = score
            if completed:
                progress_record.date_completed = datetime.utcnow()
        else:
            # Create new record
            progress_record = Progress(
                user_id=current_user.id,
                lesson_id=lesson_id,
                course_id=course_id,
                completed=completed,
                score=score
            )
            if completed:
                progress_record.date_completed = datetime.utcnow()
            db.session.add(progress_record)
        
        db.session.commit()
        
        # Check for achievements
        check_and_assign_achievements(current_user.id)
        
        return jsonify({'success': True})
    
    # GET request - return user's progress
    progress_records = Progress.query.filter_by(user_id=current_user.id).all()
    progress_data = []
    for record in progress_records:
        progress_data.append({
            'lesson_id': record.lesson_id,
            'completed': record.completed,
            'score': record.score,
            'date_completed': record.date_completed.isoformat() if record.date_completed else None
        })
    
    return jsonify({'progress': progress_data})

@app.route('/api/quiz/<int:lesson_id>')
def get_quiz(lesson_id):
    quiz = Quiz.query.filter_by(lesson_id=lesson_id).first()
    if not quiz:
        return jsonify({'error': 'No quiz found for this lesson'}), 404
    
    return jsonify({
        'id': quiz.id,
        'question': quiz.question,
        'options': quiz.options,
        'correct_answer': quiz.correct_answer
    })

def check_and_assign_achievements(user_id):
    """Check conditions and assign achievements to user if criteria are met"""
    user = User.query.get(user_id)
    
    # Count completed lessons
    completed_lessons = Progress.query.filter_by(user_id=user_id, completed=True).count()
    
    # Check for "Code Runner" achievement (5 lessons completed)
    if completed_lessons >= 5 and not Achievement.query.filter_by(user_id=user_id, name="Code Runner").first():
        achievement = Achievement(
            user_id=user_id,
            name="Code Runner",
            description="Completed 5 lessons"
        )
        db.session.add(achievement)
    
    # Check for "Problem Solver" achievement (average score > 80% on 3 quizzes)
    progress_with_scores = Progress.query.filter(
        Progress.user_id == user_id,
        Progress.score.isnot(None)
    ).all()
    
    if len(progress_with_scores) >= 3:
        avg_score = sum(p.score for p in progress_with_scores) / len(progress_with_scores)
        if avg_score >= 80 and not Achievement.query.filter_by(user_id=user_id, name="Problem Solver").first():
            achievement = Achievement(
                user_id=user_id,
                name="Problem Solver",
                description="Achieved average score of 80%+ on 3 quizzes"
            )
            db.session.add(achievement)
    
    # Check for "Week Warrior" achievement (7 consecutive days logged in)
    # Note: This is a simplified version - in a real app, you'd track daily logins
    
    db.session.commit()

@app.route('/api/run_code', methods=['POST'])
def run_code():
    """Run Java code submitted by the user"""
    data = request.get_json()
    code = data.get('code', '')
    
    if not code:
        return jsonify({'success': False, 'output': '', 'error': 'No code provided'})
    
    # Run the Java code using our JavaRunner
    result = java_runner.run_java_code(code)
    
    return jsonify(result)

@app.route('/api/quizzes/<int:lesson_id>', methods=['GET'])
def get_lesson_quiz(lesson_id):
    """Get the quiz for a specific lesson"""
    quiz = Quiz.query.filter_by(lesson_id=lesson_id).first()
    if not quiz:
        return jsonify({'error': 'No quiz found for this lesson'}), 404
    
    return jsonify({
        'id': quiz.id,
        'question': quiz.question,
        'options': quiz.options,
        'lesson_id': quiz.lesson_id
    })

@app.route('/api/quiz/submit', methods=['POST'])
def submit_quiz():
    """Submit answers to a quiz"""
    data = request.get_json()
    quiz_id = data.get('quiz_id')
    selected_answer = data.get('selected_answer')
    
    if not quiz_id or not selected_answer:
        return jsonify({'success': False, 'message': 'Missing quiz_id or selected_answer'}), 400
    
    # Get the quiz
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check if the answer is correct
    is_correct = quiz.correct_answer == selected_answer
    score = 100.0 if is_correct else 0.0
    
    # Create submission record
    submission = QuizSubmission(
        user_id=current_user.id,
        quiz_id=quiz_id,
        selected_answer=selected_answer,
        is_correct=is_correct,
        score=score
    )
    
    db.session.add(submission)
    db.session.commit()
    
    # Update progress
    lesson_id = quiz.lesson_id
    course_id = quiz.lesson.course_id
    
    # Check if progress record exists
    progress = Progress.query.filter_by(
        user_id=current_user.id,
        lesson_id=lesson_id
    ).first()
    
    if not progress:
        progress = Progress(
            user_id=current_user.id,
            lesson_id=lesson_id,
            course_id=course_id,
            completed=True,
            score=score
        )
        db.session.add(progress)
    else:
        progress.completed = True
        progress.score = score
    
    db.session.commit()
    
    # Check for achievements
    check_and_assign_achievements(current_user.id)
    
    return jsonify({
        'success': True,
        'is_correct': is_correct,
        'score': score,
        'correct_answer': quiz.correct_answer
    })

@app.route('/api/assignments/<int:lesson_id>', methods=['GET'])
def get_lesson_assignment(lesson_id):
    """Get assignments for a specific lesson"""
    assignments = Assignment.query.filter_by(lesson_id=lesson_id).all()
    
    assignment_list = []
    for assignment in assignments:
        # Check if user has submitted this assignment
        submission = AssignmentSubmission.query.filter_by(
            assignment_id=assignment.id,
            user_id=current_user.id
        ).first()
        
        assignment_data = {
            'id': assignment.id,
            'title': assignment.title,
            'description': assignment.description,
            'due_date': assignment.due_date.isoformat() if assignment.due_date else None,
            'max_score': assignment.max_score,
            'has_submitted': submission is not None,
            'score': submission.score if submission else None,
            'date_submitted': submission.date_submitted.isoformat() if submission else None
        }
        assignment_list.append(assignment_data)
    
    return jsonify({'assignments': assignment_list})

@app.route('/api/assignment/submit', methods=['POST'])
@login_required
def submit_assignment():
    """Submit an assignment"""
    data = request.get_json()
    assignment_id = data.get('assignment_id')
    code_submission = data.get('code_submission', '')
    text_submission = data.get('text_submission', '')
    
    if not assignment_id:
        return jsonify({'success': False, 'message': 'Missing assignment_id'}), 400
    
    # Check if assignment exists
    assignment = Assignment.query.get_or_404(assignment_id)
    
    # Check if user has already submitted this assignment
    existing_submission = AssignmentSubmission.query.filter_by(
        assignment_id=assignment_id,
        user_id=current_user.id
    ).first()
    
    if existing_submission:
        # Update existing submission
        existing_submission.code_submission = code_submission
        existing_submission.text_submission = text_submission
        existing_submission.date_submitted = datetime.utcnow()
    else:
        # Create new submission
        submission = AssignmentSubmission(
            assignment_id=assignment_id,
            user_id=current_user.id,
            code_submission=code_submission,
            text_submission=text_submission
        )
        db.session.add(submission)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Assignment submitted successfully'})

# Forum API routes
@app.route('/api/forum/categories', methods=['GET', 'POST'])
@login_required
def forum_categories():
    """Get all forum categories or create a new one"""
    if request.method == 'GET':
        categories = ForumCategory.query.all()
        categories_data = [{
            'id': cat.id,
            'name': cat.name,
            'description': cat.description,
            'thread_count': len(cat.threads)
        } for cat in categories]
        return jsonify({'categories': categories_data})
    
    if not (current_user.is_admin() or current_user.is_instructor()):
        return jsonify({'success': False, 'message': 'Admin or instructor access required'}), 403
    
    data = request.get_json()
    name = data.get('name')
    description = data.get('description', '')
    
    if not name:
        return jsonify({'success': False, 'message': 'Category name is required'}), 400
    
    # Check if category already exists
    existing_category = ForumCategory.query.filter_by(name=name).first()
    if existing_category:
        return jsonify({'success': False, 'message': 'Category already exists'}), 400
    
    category = ForumCategory(name=name, description=description)
    db.session.add(category)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Category created successfully', 'category_id': category.id})

@app.route('/api/forum/threads', methods=['GET', 'POST'])
@login_required
def forum_threads():
    """Get all forum threads or create a new one"""
    if request.method == 'GET':
        category_id = request.args.get('category_id')
        threads_query = ForumThread.query
        
        if category_id:
            threads_query = threads_query.filter_by(category_id=category_id)
        
        threads = threads_query.order_by(ForumThread.is_pinned.desc(), ForumThread.updated_at.desc()).all()
        
        threads_data = []
        for thread in threads:
            reply_count = len(thread.replies)
            latest_reply = max(thread.replies, key=lambda r: r.created_at) if thread.replies else None
            
            thread_data = {
                'id': thread.id,
                'title': thread.title,
                'content': thread.content[:100] + '...' if len(thread.content) > 100 else thread.content,
                'username': thread.user.username,
                'category_name': thread.category.name,
                'created_at': thread.created_at.isoformat(),
                'updated_at': thread.updated_at.isoformat(),
                'reply_count': reply_count,
                'latest_reply_at': latest_reply.created_at.isoformat() if latest_reply else None,
                'is_pinned': thread.is_pinned,
                'is_locked': thread.is_locked
            }
            threads_data.append(thread_data)
        
        return jsonify({'threads': threads_data})
    
    # POST method - Create a new thread
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')
    category_id = data.get('category_id')
    
    if not title or not content or not category_id:
        return jsonify({'success': False, 'message': 'Title, content, and category are required'}), 400
    
    # Verify category exists
    category = ForumCategory.query.get(category_id)
    if not category:
        return jsonify({'success': False, 'message': 'Category not found'}), 404
    
    thread = ForumThread(
        title=title,
        content=content,
        user_id=current_user.id,
        category_id=category_id
    )
    db.session.add(thread)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Thread created successfully', 'thread_id': thread.id})

@app.route('/api/forum/threads/<int:thread_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def forum_thread(thread_id):
    """Get, update, or delete a specific forum thread"""
    thread = ForumThread.query.get_or_404(thread_id)
    
    if request.method == 'GET':
        # Get thread with all replies
        replies = ForumReply.query.filter_by(thread_id=thread_id).order_by(ForumReply.created_at.asc()).all()
        
        thread_data = {
            'id': thread.id,
            'title': thread.title,
            'content': thread.content,
            'username': thread.user.username,
            'category_name': thread.category.name,
            'created_at': thread.created_at.isoformat(),
            'updated_at': thread.updated_at.isoformat(),
            'is_pinned': thread.is_pinned,
            'is_locked': thread.is_locked,
            'replies': [{
                'id': reply.id,
                'content': reply.content,
                'username': reply.user.username,
                'created_at': reply.created_at.isoformat(),
                'updated_at': reply.updated_at.isoformat()
            } for reply in replies]
        }
        
        return jsonify({'thread': thread_data})
    
    # Check if user can modify thread (thread owner, admin, or instructor)
    if not (current_user.id == thread.user_id or current_user.is_admin() or current_user.is_instructor()):
        return jsonify({'success': False, 'message': 'Insufficient permissions'}), 403
    
    if request.method == 'PUT':
        data = request.get_json()
        
        if 'title' in data:
            thread.title = data['title']
        if 'content' in data:
            thread.content = data['content']
        if 'is_pinned' in data and current_user.is_admin():
            thread.is_pinned = data['is_pinned']
        if 'is_locked' in data:
            thread.is_locked = data['is_locked']
        
        thread.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Thread updated successfully'})
    
    if request.method == 'DELETE':
        db.session.delete(thread)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Thread deleted successfully'})

@app.route('/api/forum/replies', methods=['POST'])
@login_required
def forum_replies():
    """Create a new reply to a thread"""
    data = request.get_json()
    content = data.get('content')
    thread_id = data.get('thread_id')
    
    if not content or not thread_id:
        return jsonify({'success': False, 'message': 'Content and thread ID are required'}), 400
    
    # Check if thread exists and is not locked
    thread = ForumThread.query.get_or_404(thread_id)
    if thread.is_locked and not current_user.is_admin():
        return jsonify({'success': False, 'message': 'This thread is locked and cannot be replied to'}), 400
    
    reply = ForumReply(
        content=content,
        user_id=current_user.id,
        thread_id=thread_id
    )
    db.session.add(reply)
    thread.updated_at = datetime.utcnow()  # Update thread's last activity time
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Reply added successfully', 'reply_id': reply.id})

# Sample data initialization
def init_sample_data():
    """Initialize sample courses, lessons, quizzes and assignments if database is empty"""
    try:
        if Course.query.count() == 0:
            # Create a sample instructor
            from flask_bcrypt import generate_password_hash
            instructor = User(
                username="instructor",
                email="instructor@example.com",
                password_hash=generate_password_hash("password").decode('utf-8'),
                role="instructor",
                is_verified=True
            )
            db.session.add(instructor)
            db.session.commit()

            # Create sample courses
            fundamentals_course = Course(
                title="Java Fundamentals",
                description="Learn the basics of Java programming: variables, data types, operators, and basic I/O.",
                level="beginner",
                instructor_id=instructor.id
            )
            oop_course = Course(
                title="Object-Oriented Programming",
                description="Dive deep into OOP concepts: classes, objects, inheritance, polymorphism, and encapsulation.",
                level="intermediate",
                instructor_id=instructor.id
            )
            advanced_course = Course(
                title="Advanced Java Concepts",
                description="Explore advanced topics: collections, streams, multithreading, and design patterns.",
                level="advanced",
                instructor_id=instructor.id
            )
            
            db.session.add_all([fundamentals_course, oop_course, advanced_course])
            db.session.commit()
            
            # Create sample lessons for fundamentals course
            lessons_fundamentals = [
                {
                    "title": "Introduction to Variables",
                    "content": "A variable is a container that holds a value which can change during program execution. In Java, variables must be declared with a specific data type before they can be used."
                },
                {
                    "title": "Basic Arithmetic Operations",
                    "content": "Learn how to perform basic mathematical operations in Java: addition, subtraction, multiplication, and division."
                },
                {
                    "title": "Conditional Statements",
                    "content": "Conditional statements allow your program to make decisions. The 'if-else' statement executes different blocks of code based on whether a condition is true or false."
                },
                {
                    "title": "Loops and Iteration",
                    "content": "Loops allow you to execute a block of code repeatedly. The 'for' loop is commonly used when you know how many times you want to repeat the code."
                },
                {
                    "title": "Arrays and Collections",
                    "content": "Arrays are used to store multiple values in a single variable, instead of declaring separate variables for each value."
                }
            ]
            
            for i, lesson_data in enumerate(lessons_fundamentals, 1):
                lesson = Lesson(
                    title=lesson_data["title"],
                    content=lesson_data["content"],
                    course_id=fundamentals_course.id,
                    lesson_number=i
                )
                db.session.add(lesson)
            
            # Create sample lessons for OOP course
            lessons_oop = [
                {
                    "title": "Classes and Objects",
                    "content": "In object-oriented programming, a class is a blueprint for creating objects. An object is an instance of a class."
                },
                {
                    "title": "Inheritance",
                    "content": "Inheritance allows us to define a class that inherits all the methods and properties from another class."
                },
                {
                    "title": "Encapsulation",
                    "content": "Encapsulation is one of the fundamental concepts in object-oriented programming (OOP). It describes the idea of wrapping data and the methods that work on data within one unit."
                },
                {
                    "title": "Polymorphism",
                    "content": "Polymorphism means 'many forms', and it occurs when we have many classes that are related to each other through inheritance."
                }
            ]
            
            for i, lesson_data in enumerate(lessons_oop, 1):
                lesson = Lesson(
                    title=lesson_data["title"],
                    content=lesson_data["content"],
                    course_id=oop_course.id,  # Fixed to use correct variable
                    lesson_number=i
                )
                db.session.add(lesson)
            
            # Create sample lessons for advanced course
            lessons_advanced = [
                {
                    "title": "Collections Framework",
                    "content": "The Java Collections Framework provides a well-designed set of interfaces and classes for storing and manipulating groups of data."
                },
                {
                    "title": "Streams API",
                    "content": "The Stream API introduced in Java 8 provides a declarative way to process collections of data."
                },
                {
                    "title": "Multithreading",
                    "content": "Multithreading is a Java feature that allows concurrent execution of two or more parts of a program for maximum utilization of CPU."
                }
            ]
            
            for i, lesson_data in enumerate(lessons_advanced, 1):
                lesson = Lesson(
                    title=lesson_data["title"],
                    content=lesson_data["content"],
                    course_id=advanced_course.id,  # Fixed to use correct variable
                    lesson_number=i
                )
                db.session.add(lesson)
            
            # Create sample quizzes
            quiz1 = Quiz(
                title="Java Variable Declaration",
                lesson_id=1,
                question="Which of the following is the correct way to declare an integer variable in Java?",
                options=["var number = 5;", "int number = 5;", "integer number = 5;", "number int = 5;"],
                correct_answer="B"
            )
            
            quiz2 = Quiz(
                title="Java Data Types",
                lesson_id=1,
                question="What is the purpose of the 'double' data type in Java?",
                options=["To store whole numbers", "To store decimal numbers", "To store text", "To store boolean values"],
                correct_answer="B"
            )
            
            quiz3 = Quiz(
                title="Conditional Expressions",
                lesson_id=3,
                question="What is the result of the expression: 10 > 5 ?",
                options=["true", "false", "10", "5"],
                correct_answer="A"
            )
            
            quiz4 = Quiz(
                title="Java Comparison Operators",
                lesson_id=3,
                question="Which operator is used for equality comparison in Java?",
                options=["=", "==", "!=", ">"],
                correct_answer="B"
            )
            
            # Create sample assignments
            assignment1 = Assignment(
                title="Variable Declaration Practice",
                description="Create a Java program that declares and initializes variables of different data types (int, double, String, boolean). Print the values of these variables to the console.",
                course_id=fundamentals_course.id,
                lesson_id=1,
                max_score=100
            )
            
            assignment2 = Assignment(
                title="Calculator Program",
                description="Create a Java program that performs basic arithmetic operations (addition, subtraction, multiplication, division) on two numbers entered by the user.",
                course_id=fundamentals_course.id,
                lesson_id=2,
                max_score=100
            )
            
            assignment3 = Assignment(
                title="Grade Determination Program",
                description="Write a Java program that takes marks of three subjects as input and determines the grade based on the percentage.",
                course_id=fundamentals_course.id,
                lesson_id=3,
                max_score=100
            )
            
            db.session.add_all([quiz1, quiz2, quiz3, quiz4, assignment1, assignment2, assignment3])
            db.session.commit()
    except Exception as e:
        print(f"Error initializing sample data: {e}")
        db.session.rollback()

with app.app_context():
    try:
        db.create_all()
        init_sample_data()
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Error initializing database: {e}")


# Admin Dashboard Route
@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    courses = Course.query.all()
    lessons = Lesson.query.all()
    quizzes = Quiz.query.all()
    assignments = Assignment.query.all()
    return render_template('admin/dashboard.html', courses=courses, lessons=lessons, quizzes=quizzes, assignments=assignments)

# Course Management
@app.route('/admin/add_course', methods=['GET', 'POST'])
@login_required
@admin_required
def add_course():
    form = CourseForm()
    if form.validate_on_submit():
        course = Course(
            title=form.title.data,
            description=form.description.data,
            level=form.level.data,
            category=form.category.data,
            instructor=current_user
        )
        db.session.add(course)
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/add_course.html', form=form)

@app.route('/admin/edit_course/<int:course_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    form = CourseForm()
    if form.validate_on_submit():
        course.title = form.title.data
        course.description = form.description.data
        course.level = form.level.data
        course.category = form.category.data
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    elif request.method == 'GET':
        form.title.data = course.title
        form.description.data = course.description
        form.level.data = course.level
        form.category.data = course.category
    return render_template('admin/edit_course.html', form=form, course=course)

@app.route('/admin/delete_course/<int:course_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

# Lesson Management
@app.route('/admin/add_lesson/<int:course_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def add_lesson(course_id):
    course = Course.query.get_or_404(course_id)
    form = LessonForm()
    if form.validate_on_submit():
        lesson = Lesson(
            title=form.title.data,
            content=form.content.data,
            lesson_type=form.lesson_type.data,
            course_id=course.id,
            lesson_number=form.lesson_number.data,
            multimedia_url=form.multimedia_url.data,
            duration=form.duration.data
        )
        db.session.add(lesson)
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/add_lesson.html', form=form, course=course)

@app.route('/admin/edit_lesson/<int:lesson_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    form = LessonForm()
    if form.validate_on_submit():
        lesson.title = form.title.data
        lesson.content = form.content.data
        lesson.lesson_type = form.lesson_type.data
        lesson.lesson_number = form.lesson_number.data
        lesson.multimedia_url = form.multimedia_url.data
        lesson.duration = form.duration.data
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    elif request.method == 'GET':
        form.title.data = lesson.title
        form.content.data = lesson.content
        form.lesson_type.data = lesson.lesson_type
        form.lesson_number.data = lesson.lesson_number
        form.multimedia_url.data = lesson.multimedia_url
        form.duration.data = lesson.duration
    return render_template('admin/edit_lesson.html', form=form, lesson=lesson)

@app.route('/admin/delete_lesson/<int:lesson_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    db.session.delete(lesson)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

# Note Management
@app.route('/admin/add_note/<int:lesson_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def add_note(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    form = NoteForm()
    if form.validate_on_submit():
        note = Note(
            title=form.title.data,
            content=form.content.data,
            lesson_id=lesson.id
        )
        db.session.add(note)
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/add_note.html', form=form, lesson=lesson)

@app.route('/admin/edit_note/<int:note_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_note(note_id):
    note = Note.query.get_or_404(note_id)
    form = NoteForm()
    if form.validate_on_submit():
        note.title = form.title.data
        note.content = form.content.data
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    elif request.method == 'GET':
        form.title.data = note.title
        form.content.data = note.content
    return render_template('admin/edit_note.html', form=form, note=note)

@app.route('/admin/delete_note/<int:note_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    db.session.delete(note)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

# Quiz Management
@app.route('/admin/add_quiz/<int:lesson_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def add_quiz(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    form = QuizForm()
    if form.validate_on_submit():
        quiz = Quiz(
            title=form.title.data,
            lesson_id=lesson.id,
            question=form.question.data,
            options={
                'A': form.option_a.data,
                'B': form.option_b.data,
                'C': form.option_c.data,
                'D': form.option_d.data
            },
            correct_answer=form.correct_answer.data,
            points=form.points.data,
            time_limit=form.time_limit.data
        )
        db.session.add(quiz)
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/add_quiz.html', form=form, lesson=lesson)

@app.route('/admin/edit_quiz/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    form = QuizForm()
    if form.validate_on_submit():
        quiz.title = form.title.data
        quiz.question = form.question.data
        quiz.options = {
            'A': form.option_a.data,
            'B': form.option_b.data,
            'C': form.option_c.data,
            'D': form.option_d.data
        }
        quiz.correct_answer = form.correct_answer.data
        quiz.points = form.points.data
        quiz.time_limit = form.time_limit.data
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    elif request.method == 'GET':
        form.title.data = quiz.title
        form.question.data = quiz.question
        form.option_a.data = quiz.options['A']
        form.option_b.data = quiz.options['B']
        form.option_c.data = quiz.options['C']
        form.option_d.data = quiz.options['D']
        form.correct_answer.data = quiz.correct_answer
        form.points.data = quiz.points
        form.time_limit.data = quiz.time_limit
    return render_template('admin/edit_quiz.html', form=form, quiz=quiz)

@app.route('/admin/delete_quiz/<int:quiz_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    db.session.delete(quiz)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

# Assignment Management
@app.route('/admin/add_assignment/<int:lesson_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def add_assignment(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    form = AssignmentForm()
    if form.validate_on_submit():
        assignment = Assignment(
            title=form.title.data,
            description=form.description.data,
            course_id=lesson.course_id,
            lesson_id=lesson.id,
            assignment_type=form.assignment_type.data,
            due_date=datetime.strptime(form.due_date.data, '%Y-%m-%d %H:%M:%S') if form.due_date.data else None,
            max_score=form.max_score.data
        )
        db.session.add(assignment)
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/add_assignment.html', form=form, lesson=lesson)

@app.route('/admin/edit_assignment/<int:assignment_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_assignment(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    form = AssignmentForm()
    if form.validate_on_submit():
        assignment.title = form.title.data
        assignment.description = form.description.data
        assignment.assignment_type = form.assignment_type.data
        assignment.due_date = datetime.strptime(form.due_date.data, '%Y-%m-%d %H:%M:%S') if form.due_date.data else None
        assignment.max_score = form.max_score.data
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    elif request.method == 'GET':
        form.title.data = assignment.title
        form.description.data = assignment.description
        form.assignment_type.data = assignment.assignment_type
        form.due_date.data = assignment.due_date.strftime('%Y-%m-%d %H:%M:%S') if assignment.due_date else ''
        form.max_score.data = assignment.max_score
    return render_template('admin/edit_assignment.html', form=form, assignment=assignment)

@app.route('/admin/delete_assignment/<int:assignment_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_assignment(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    db.session.delete(assignment)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8000, use_reloader=False)
