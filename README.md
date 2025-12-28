# Java Mastery Platform

A comprehensive learning management system for Java programming with interactive lessons, quizzes, assignments, and code execution capabilities.

## Features

- Interactive Java lessons with code execution
- Quizzes and assignments
- Progress tracking
- Admin panel for content management
- User authentication and authorization
- Forum for discussions
- Multi-factor authentication

## Prerequisites for Vercel Deployment

Before deploying to Vercel, you need to set up:

1. **Database**: PostgreSQL database (REQUIRED: Supabase for proper Vercel integration)
2. **Environment Variables**: Properly configured environment variables
3. **Secret Key**: A secure SECRET_KEY for session management

## Deployment to Vercel

### Step 1: Set Up Supabase Database (Required)

This application requires a PostgreSQL database and will NOT work with SQLite on Vercel. You must set up a Supabase database:

1. Go to [supabase.io](https://supabase.io) and create a new project
2. Create a new Supabase project with a region close to your users
3. After your project is ready, go to Project Settings → Database
4. Copy the connection string (Postgres URL) - it looks like: `postgresql://[user]:[password]@[host]:[port]/[database]`
5. Create the required tables by running the following SQL in the Supabase SQL Editor:

```sql
-- Create tables using the same schema as defined in the Flask models
CREATE TABLE user (
    id SERIAL PRIMARY KEY,
    username VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(60) NOT NULL,
    role VARCHAR(20) DEFAULT 'student',
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    totp_secret VARCHAR(32),
    is_2fa_enabled BOOLEAN DEFAULT FALSE
);

CREATE TABLE course (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    level VARCHAR(20) NOT NULL,
    category VARCHAR(50) DEFAULT 'General',
    instructor_id INTEGER REFERENCES user(id),
    status VARCHAR(20) DEFAULT 'draft',
    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE lesson (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    lesson_type VARCHAR(20) DEFAULT 'text',
    course_id INTEGER NOT NULL REFERENCES course(id),
    lesson_number INTEGER NOT NULL,
    multimedia_url VARCHAR(200),
    duration INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'draft',
    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add other tables as needed based on the Flask models...
```

### Step 2: Generate a SECRET_KEY

The SECRET_KEY is critical for session management and must be set as an environment variable:

```bash
python -c 'import secrets; print(secrets.token_hex(16))'
```

Generate a random string and save it securely - you'll need this for the environment variables.

### Step 3: Deploy to Vercel

1. Fork or clone this repository to your GitHub account
2. Go to [vercel.com](https://vercel.com) and sign in
3. Click "New Project" and import your forked repository
4. During the setup process, you'll need to add the following environment variables:

#### Required Environment Variables

Add these environment variables in your Vercel project settings under "Settings" → "Environment Variables":

- `DATABASE_URL`: Your Supabase PostgreSQL connection string (format: `postgresql://username:password@host:port/database_name`)
- `SECRET_KEY`: The secret key you generated earlier (IMPORTANT: This must be set for the application to work properly on Vercel!)

#### Optional Environment Variables

- `MAIL_SERVER`: Email server for notifications (default: smtp.gmail.com)
- `MAIL_PORT`: Email server port (default: 587)
- `MAIL_USE_TLS`: Enable TLS (default: True)
- `MAIL_USERNAME`: Email username
- `MAIL_PASSWORD`: Email password
- `MAIL_DEFAULT_SENDER`: Default sender email address

### Step 4: Complete the Deployment

1. Make sure the build command is set to `pip install -r requirements.txt`
2. Set the output directory appropriately
3. Click "Deploy"

## Why the SECRET_KEY is Critical

The login issue on Vercel occurs because of how serverless functions work:

- On traditional servers, the application runs continuously, keeping session information stable
- On Vercel (serverless), each request may hit a completely new instance of your application
- Without a consistent SECRET_KEY across all instances, session data becomes incompatible between requests
- This causes login sessions to be lost immediately after login

Setting the SECRET_KEY as an environment variable ensures all serverless instances use the same key for session encryption.

## Why Supabase PostgreSQL is Required

Unlike traditional hosting, Vercel serverless functions cannot use SQLite because:

- SQLite is a file-based database that doesn't work with ephemeral serverless functions
- Each serverless function instance gets destroyed after processing a request
- File-based persistence is impossible in Vercel's ephemeral environment
- A managed PostgreSQL database like Supabase provides persistent storage that works with Vercel

## Troubleshooting

### Common Issues

**Issue**: Login works locally but fails on Vercel
**Solution**: Ensure `SECRET_KEY` is properly set in Vercel environment variables

**Issue**: Database connection errors
**Solution**: Verify your `DATABASE_URL` is correctly formatted and accessible. Make sure you're using Supabase PostgreSQL, not SQLite.

**Issue**: Login immediately expires after successful login
**Solution**: Check that `SECRET_KEY` is set and remains consistent across deployments

**Issue**: Application crashes with "SQLite is not supported" error
**Solution**: Make sure you have properly set the `DATABASE_URL` environment variable with your Supabase connection string

### Debugging Steps

1. Check Vercel logs: Go to your project in Vercel dashboard → Logs
2. Verify environment variables: Project Settings → Environment Variables
3. Test database connectivity separately
4. Ensure your database allows connections from external sources

## Local Development

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set environment variables in a `.env` file or system environment:
   ```
   DATABASE_URL=postgresql://username:password@localhost:5432/javamastery_db  # Use PostgreSQL locally too
   SECRET_KEY=your_generated_secret_key
   ```
4. Run the application: `python app.py`

## Technologies Used

- Flask
- SQLAlchemy
- PostgreSQL
- HTML/CSS/JavaScript
- Bootstrap

## Contributing

Feel free to submit issues and enhancement requests!

## License

MIT.
