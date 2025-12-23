# Java Mastery Platform

A comprehensive learning management system for Java programming with interactive lessons, quizzes, assignments, and code execution capabilities.

## Deployment to Vercel

This application is designed for deployment to Vercel with persistent database storage.

### Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **Database**: Set up a PostgreSQL database (recommended: Supabase or Neon)
3. **Environment Variables**: Configure the required environment variables

### Environment Variables Required

Add these environment variables in your Vercel project settings:

- `DATABASE_URL`: PostgreSQL connection string (format: `postgresql://username:password@host:port/database_name`)
- `SECRET_KEY`: A random secret key for session management (IMPORTANT: This must be set for Vercel deployment to work properly!)
- `MAIL_SERVER`: Email server for notifications (optional)
- `MAIL_PORT`: Email server port (optional)
- `MAIL_USERNAME`: Email username (optional)
- `MAIL_PASSWORD`: Email password (optional)

### Setting up the SECRET_KEY

The `SECRET_KEY` is critical for session management and must be set as an environment variable. If not set, the application will fail on Vercel due to inconsistent session handling across serverless function invocations.

To generate a secure SECRET_KEY:

```bash
python -c 'import secrets; print(secrets.token_hex(16))'
```

### Deployment Steps

1. Fork or clone this repository
2. Import the project into Vercel
3. In the Vercel dashboard, add the required environment variables
4. Deploy the project

### Database Setup

For PostgreSQL database, you can use:

- **Supabase** (Recommended): [supabase.com](https://supabase.com)
- **Neon**: [neon.tech](https://neon.tech)

After setting up your database, use the connection string as your `DATABASE_URL`.

### Troubleshooting

**Issue**: Login works locally but fails on Vercel
**Solution**: Ensure `SECRET_KEY` is properly set in Vercel environment variables. Without a consistent secret key, sessions will not persist properly on Vercel's serverless architecture.

**Issue**: Database connection errors
**Solution**: Verify your `DATABASE_URL` is correctly formatted and accessible.

## Features

- Interactive Java lessons with code execution
- Quizzes and assignments
- Progress tracking
- Admin panel for content management
- User authentication and authorization
- Forum for discussions
- Multi-factor authentication

## Local Development

1. Install dependencies: `pip install -r requirements.txt`
2. Set environment variables
3. Run: `python app.py`

## Technologies Used

- Flask
- SQLAlchemy
- PostgreSQL
- HTML/CSS/JavaScript
- Bootstrap

## License

MIT
