"""
Database models for Java Mastery LMS
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta
import secrets

db = SQLAlchemy()

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
    correct_answer = db.Column(db.String(1), nullable=False) # A, B, C, or D
    points = db.Column(db.Integer, default=1)  # Points for correct answer
    time_limit = db.Column(db.Integer, default=0)  # Time limit in seconds, 0 = no limit
    status = db.Column(db.String(20), default='active') # active, inactive
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
    status = db.Column(db.String(20), default='active') # active, inactive, closed
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

# New model for lesson notes
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(10), nullable=False)
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
    status = db.Column(db.String(20), default='pending') # pending, approved, rejected
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