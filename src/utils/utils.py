"""
Utility functions for Java Mastery LMS
"""
import secrets
import re
from datetime import datetime, timedelta
from flask_mail import Message
from flask import url_for


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


def send_reset_email(user, mail, PasswordResetToken, db):
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


def verify_reset_token(token, PasswordResetToken):
    """Verify the password reset token"""
    reset_token = PasswordResetToken.query.filter_by(token=token).first()
    
    if not reset_token or reset_token.used or reset_token.expires_at < datetime.utcnow():
        return None
    
    return reset_token.user


def generate_totp_secret():
    """Generate a secret for TOTP-based 2FA"""
    import pyotp
    return pyotp.random_base32()


def verify_totp_token(secret, token):
    """Verify a TOTP token"""
    import pyotp
    totp = pyotp.TOTP(secret)
    return totp.verify(token)


def check_and_assign_achievements(user_id, db, User, Progress, Achievement):
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


def update_enrollment_status(course_id, user_id, db, Course, Lesson, Progress, Enrollment, Notification):
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