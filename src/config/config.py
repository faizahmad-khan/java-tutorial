import os
import secrets
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix


class Config:
    """Base configuration class"""
    
    # Secret key - ensure it's set in production environments
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        # For development only - warn in production
        SECRET_KEY = os.environ.get('DEV_SECRET_KEY', secrets.token_hex(16))
        if not os.environ.get('FLASK_ENV') == 'development':
            print("WARNING: SECRET_KEY not set in environment! This should be set for production.")

    # Database configuration
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL:
        # For production (PostgreSQL)
        SQLALCHEMY_DATABASE_URI = DATABASE_URL.replace("postgres://", "postgresql://")
    else:
        # For development (SQLite)
        SQLALCHEMY_DATABASE_URI = 'sqlite:///javamastery.db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session configuration for production
    SESSION_COOKIE_SECURE = True  # Use secure cookies in production
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Mail configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Enhanced security for production
    SESSION_COOKIE_SECURE = True  # Ensure HTTPS cookies
    PREFERRED_URL_SCHEME = 'https'
    
    # Detect Vercel environment and apply specific settings
    IS_VERCEL = os.environ.get('VERCEL', False) or os.environ.get('VERCEL_ENV', False) or os.environ.get('NOW_REGION', False)
    
    if IS_VERCEL:
        # Additional Vercel-specific configurations
        TRAP_HTTP_EXCEPTIONS = True


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    
    # For development, we can use insecure cookies
    SESSION_COOKIE_SECURE = False


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


def create_app(config_class=ProductionConfig):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Apply proxy fix for Vercel and other reverse proxy environments
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    return app