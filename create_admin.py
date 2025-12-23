from app import app, db, User
from flask_bcrypt import Bcrypt


def create_admin_user():
    """Create an admin user account"""
    with app.app_context():
        bcrypt = Bcrypt()
        
        # Check if admin user already exists
        existing_admin = User.query.filter_by(role='admin').first()
        if existing_admin:
            print(f"Admin user already exists: {existing_admin.username}")
            return
        
        # Create admin user
        username_input = input("Enter admin username (default: admin): ")
        admin_username = username_input or "admin"
        email_input = input("Enter admin email (default: admin@example.com): ")
        admin_email = email_input or "admin@example.com"
        admin_password = input("Enter admin password: ")
        
        if not admin_password:
            print("Password is required!")
            return
            
        # Hash the password
        hashed_password = bcrypt.generate_password_hash(
            admin_password
        ).decode('utf-8')
        
        # Create the admin user
        admin_user = User(
            username=admin_username,
            email=admin_email,
            password_hash=hashed_password,
            role='admin',
            is_verified=True
        )
        
        db.session.add(admin_user)
        db.session.commit()
        
        print(f"Admin user '{admin_username}' created successfully!")


if __name__ == "__main__":
    create_admin_user()