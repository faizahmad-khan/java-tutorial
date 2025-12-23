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

1. **Database**: PostgreSQL database (recommended: Supabase or Neon)
2. **Environment Variables**: Properly configured environment variables
3. **Secret Key**: A secure SECRET_KEY for session management

## Deployment to Vercel

### Step 1: Prepare Your Database

You'll need a PostgreSQL database. Recommended options:

- [Supabase](https://supabase.com) (Free tier available)
- [Neon](https://neon.tech) (Free tier available)

After setting up your database, copy the connection string (format: `postgresql://username:password@host:port/database_name`).

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

- `DATABASE_URL`: Your PostgreSQL connection string (format: `postgresql://username:password@host:port/database_name`)
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

## Troubleshooting

### Common Issues

**Issue**: Login works locally but fails on Vercel
**Solution**: Ensure `SECRET_KEY` is properly set in Vercel environment variables

**Issue**: Database connection errors
**Solution**: Verify your `DATABASE_URL` is correctly formatted and accessible

**Issue**: Login immediately expires after successful login
**Solution**: Check that `SECRET_KEY` is set and remains consistent across deployments

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
   DATABASE_URL=sqlite:///javamastery.db  # For local development
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

MIT
