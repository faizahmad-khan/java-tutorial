"""
Database initialization script for the Java Mastery Platform.

This script can be used to initialize the database with the required tables
and sample data. It's especially useful for production deployments.
"""

from app import app, db
from app import init_sample_data # Assuming init_sample_data is defined in app.py

def initialize_database():
    """Initialize the database with tables and sample data."""
    with app.app_context():
        try:
            # Create all database tables
            db.create_all()
            print("Database tables created successfully!")
            
            # Initialize sample data
            init_sample_data()
            print("Sample data initialized successfully!")
            
            print("\nDatabase initialization completed successfully!")
            print("You can now run the application with 'python app.py'")
            
        except Exception as e:
            print(f"Error during database initialization: {e}")
            return False
    
    return True

if __name__ == "__main__":
    print("Initializing database for Java Mastery Platform...")
    success = initialize_database()
    
    if success:
        print("\n✓ Database initialization completed successfully!")
        print("The application is ready to use.")
    else:
        print("\n✗ Database initialization failed!")
        print("Please check the error messages above and try again.")