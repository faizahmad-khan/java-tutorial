from app import app, db, User
from flask_bcrypt import Bcrypt


def add_default_admin():
    """Add a default admin user if none exists"""
    with app.app_context():
        bcrypt = Bcrypt()
        
        # Check if any admin user exists
        admin_user = User.query.filter_by(role='admin').first()
        if admin_user:
            print(f"Admin user already exists: {admin_user.username}")
            return
        
        # Create default admin user
        password = "admin123"
        hashed_password = bcrypt.generate_password_hash(
            password
        ).decode('utf-8')
        default_admin = User(
            username="admin",
            email="admin@example.com",
            password_hash=hashed_password,
            role="admin",
            is_verified=True
        )
        
        db.session.add(default_admin)
        db.session.commit()
        
        print("Default admin user created successfully!")
        print("Username: admin")
        print("Email: admin@example.com")
        print("Password: admin123")


if __name__ == "__main__":
    add_default_admin()