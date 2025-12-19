# Java Mastery Platform

A comprehensive Java learning platform that guides users from absolute beginner level to advanced proficiency through a structured curriculum. The platform features interactive coding environments, progress tracking, assessments, and social learning features.

## Features

### Core Features
- **Structured Curriculum**: Beginner to advanced Java lessons with a logical progression
- **Interactive Code Editor**: Real-time code execution with syntax highlighting
- **Progress Tracking**: Detailed analytics and achievement badges
- **Assessment System**: Quizzes and assignments with automatic grading
- **Video Tutorials**: High-quality instructional videos with closed captions
- **Certificate Generation**: Automated certificates upon course completion

### Technical Features
- **Secure Authentication**: Role-based access control with user management
- **Responsive Design**: Optimized for desktop, tablet, and mobile devices
- **Cross-browser Compatibility**: Works across all modern browsers
- **Accessibility**: Compliant with WCAG guidelines
- **Performance Optimized**: Fast loading times and efficient resource usage

### Social Features
- **Discussion Forums**: Topic-based discussion threads
- **Peer Collaboration**: Code sharing and review capabilities
- **Live Chat**: Real-time communication with instructors and peers

## Technology Stack

### Backend
- **Python Flask**: Web framework for backend services
- **SQLAlchemy**: Database ORM for data persistence
- **Flask-Login**: User session management
- **Flask-Bcrypt**: Password hashing and security

### Frontend
- **HTML5/CSS3/JavaScript**: Core web technologies
- **Ace Editor**: Advanced code editor with syntax highlighting
- **Chart.js**: Data visualization for progress tracking
- **Bootstrap**: Responsive layout framework

### Java Execution
- **Secure Java Runner**: Sandboxed Java code execution environment
- **Process Management**: Safe execution with timeout and resource limits

## Installation

### Prerequisites
- Python 3.8 or higher
- Java Development Kit (JDK) 8 or higher
- pip (Python package manager)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd java-mastery-platform
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the platform**
   Open your browser and navigate to `http://127.0.0.1:5000`
   
   Or click here to access the live application: [Java Mastery Platform](http://127.0.0.1:3000/index.html)

## Project Structure

```
java-mastery-platform/
│
├── app.py                 # Main Flask application
├── java_runner.py         # Secure Java execution environment
├── requirements.txt       # Python dependencies
├── DEPLOYMENT.md          # Deployment guide
├── static/                # Static assets
│   ├── css/              # Stylesheets
│   ├── js/               # JavaScript files
│   ├── images/           # Image assets
│   └── videos/           # Video tutorials
├── templates/            # HTML templates
│   ├── base.html         # Base template
│   ├── index.html        # Home page
│   ├── login.html        # Login page
│   ├── register.html     # Registration page
│   ├── profile.html      # User profile
│   ├── dashboard.html    # Learning dashboard
│   ├── forum.html        # Discussion forum
│   └── admin.html        # Admin panel
└── LECTURE/              # Original Java lecture files
    ├── class1.java       # Basic arithmetic
    ├── class2.java       # Conditional logic
    ├── class3.java       # Prime number check
    ├── class4.java       # Array operations
    ├── class5.java       # Array sum
    ├── class6.java       # Nested loops
    ├── class7.java       # String manipulation
    └── class8.java       # Methods
```

## Database Schema

The application uses SQLAlchemy ORM with the following models:

- **User**: User accounts and authentication
- **Course**: Learning paths (beginner, intermediate, advanced)
- **Lesson**: Individual lessons within courses
- **Progress**: User progress tracking
- **Achievement**: Badges and accomplishments
- **Quiz**: Assessment questions
- **Assignment**: Coding assignments
- **ForumPost**: Discussion forum posts

## API Endpoints

### Authentication
- `POST /login` - User login
- `POST /register` - User registration
- `GET /logout` - User logout

### Learning Content
- `GET /` - Home page with courses
- `GET /dashboard` - Learning analytics dashboard
- `GET /forum` - Discussion forum
- `GET /admin` - Admin panel

### Progress Tracking
- `GET /api/progress` - Get user progress
- `POST /api/progress` - Update user progress
- `POST /api/run_code` - Execute Java code
- `POST /api/quiz/submit` - Submit quiz answers

### Content Management
- `GET /api/courses` - Get all courses
- `POST /api/courses` - Create new course
- `GET /api/lessons` - Get all lessons
- `POST /api/lessons` - Create new lesson
- `GET /api/quizzes` - Get all quizzes
- `POST /api/quizzes` - Create new quiz

## Security Features

- **Input Sanitization**: All user inputs are validated and sanitized
- **Secure Code Execution**: Java code runs in a sandboxed environment
- **Session Management**: Secure session handling with Flask-Login
- **Password Security**: Bcrypt for password hashing
- **SQL Injection Prevention**: SQLAlchemy ORM prevents SQL injection

## Development Guidelines

### Code Style
- Follow PEP 8 for Python code
- Use consistent naming conventions
- Write comprehensive docstrings
- Include unit tests for critical functionality

### Frontend Best Practices
- Mobile-first responsive design
- Semantic HTML structure
- Accessible UI components
- Performance-optimized assets

## Testing

The platform includes comprehensive testing for:
- User authentication and authorization
- Code execution safety
- Progress tracking accuracy
- Database operations
- API endpoint functionality

## Performance Optimization

- Database query optimization with proper indexing
- Asset minification and compression
- Efficient caching strategies
- Asynchronous operations for long-running tasks

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please contact [support-email] or create an issue in the repository.

## Acknowledgments

- Original Java lecture files provided by faizahmad-khan
- Ace Editor for the code editor component
- Chart.js for data visualization
- Flask community for the web framework

---

**Note**: This platform was developed based on the Java tutorial files in the LECTURE directory, expanding them into a comprehensive learning management system with interactive features, progress tracking, and social learning capabilities.
