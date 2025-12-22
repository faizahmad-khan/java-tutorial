# Java Mastery Platform

A comprehensive Java learning platform with interactive code execution, progress tracking, quizzes, assignments, and an admin panel for content management.

## 🚀 Quick Access

**Access the platform here:** [https://java-tutorial-steel.vercel.app](https://java-tutorial-steel.vercel.app)

## Features

- **Interactive Code Editor**: Real-time Java code execution with syntax highlighting
- **Structured Curriculum**: Beginner to advanced lessons
- **Progress Tracking**: Analytics and achievement badges
- **Quizzes & Assignments**: Automated grading
- **Discussion Forum**: Community learning
- **Admin Panel**: Content management system
- **Secure Authentication**: Role-based access control

## Technology Stack

- **Backend**: Python Flask, SQLAlchemy ORM
- **Frontend**: HTML5, CSS3, JavaScript, Ace Editor
- **Database**: SQLite (development), PostgreSQL (production)
- **Java Execution**: Secure sandboxed Java runner

## Installation & Setup

### Prerequisites
- Python 3.8+
- Java Development Kit (JDK 8+)
- pip (Python package manager)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/faizahmad-khan/java-tutorial.git
   cd java-tutorial
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip3 install -r requirements.txt
   ```

4. **Initialize the database**
   ```bash
   python3 init_db.py
   ```

5. **Run the application**
   ```bash
   python3 app.py
   ```

5. **Access the platform**
   Open your browser and go to **[https://java-tutorial-steel.vercel.app](https://java-tutorial-steel.vercel.app)**

## Getting Started

### For Students
1. Visit https://java-tutorial-steel.vercel.app
2. Click "Sign Up" to create an account
3. Browse and enroll in courses
4. Track your progress on the dashboard
5. Complete quizzes and assignments

### For Instructors/Admins
1. Login to your admin account
2. Navigate to `/admin` in the navbar
3. Manage courses, lessons, quizzes, and assignments
4. Monitor student progress and provide feedback

## Project Structure

```
java-tutorial/
├── app.py                      # Main Flask application
├── java_runner.py              # Java execution environment
├── requirements.txt            # Python dependencies
├── templates/                  # HTML templates
│   ├── admin/                  # Admin panel templates
│   ├── index.html              # Home page
│   ├── login.html              # Login page
│   ├── register.html           # Registration
│   ├── dashboard.html          # Student dashboard
│   ├── forum.html              # Discussion forum
│   └── base.html               # Base template
├── static/                     # Static assets
│   ├── styles.css              # Stylesheets
│   ├── script.js               # JavaScript
│   └── dark-theme.css          # Dark theme
└── LECTURE/                    # Java tutorial files
    ├── class1.java to class8.java
    └── hello.java
```

## Core Functionality

### User Management
- User registration and login
- Profile management
- Role-based access control (Student, Instructor, Admin)

### Learning Content
- Create and manage courses
- Add lessons with multimedia
- Create quizzes with questions
- Post assignments with deadlines
- Track student progress

### Interactive Features
- Real-time Java code execution
- Code editor with syntax highlighting
- Progress dashboards
- Discussion forums

## Security

- Password hashing with bcrypt
- Secure session management
- Protected admin routes
- Input validation and sanitization
- Sandboxed Java code execution

## Deployment

For production deployment, see [DEPLOYMENT.md](DEPLOYMENT.md)

### Vercel Deployment with PostgreSQL

To deploy this application with persistent database storage on Vercel:

1. **Set up a PostgreSQL database** (recommended options):
   - [Supabase](https://supabase.com/) (free tier available)
   - [Neon](https://neon.tech/) (free tier available)
   - [AWS RDS](https://aws.amazon.com/rds/)
   - [Google Cloud SQL](https://cloud.google.com/sql)

2. **Configure environment variables in Vercel**:
   - `DATABASE_URL`: Your PostgreSQL connection string (format: postgresql://username:password@host:port/database_name)

3. **Deploy to Vercel**:
   - Connect your GitHub repository to Vercel
   - The application will automatically use PostgreSQL in production and SQLite for local development

### Local Development
For local development, the application will continue to use SQLite as configured in the code.

Supported platforms:
- Heroku
- AWS Elastic Beanstalk
- Google Cloud Platform
- Azure App Service
- DigitalOcean
- Render
- Vercel (with PostgreSQL)

## Troubleshooting

**Port already in use?**
```bash
killall python3
python3 app.py
```

**Database errors?**
The database is created automatically. To reset:
```bash
rm instance/javamastery.db
python3 app.py
```

**Import errors?**
Install all dependencies:
```bash
pip3 install -r requirements.txt
```

---

**Version:** 1.0.0 | **Last Updated:** December 2025
