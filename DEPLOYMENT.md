# Deployment Guide

This guide provides instructions for deploying the Java Mastery Platform to various hosting platforms with persistent database storage.

## Vercel Deployment with PostgreSQL

### Option 1: Using Supabase (Recommended)

1. **Create a Supabase account**:
   - Go to [supabase.com](https://supabase.com)
   - Sign up for a free account
   - Create a new project

2. **Get your database connection string**:
   - In your Supabase project dashboard
   - Go to Project Settings → Database
   - Copy the connection string (PostgreSQL format)

3. **Deploy to Vercel**:
   - Connect your GitHub repository to Vercel
   - In your Vercel project settings, go to Environment Variables
   - Add a new variable:
     - Key: `DATABASE_URL`
     - Value: Your Supabase connection string
   - Redeploy your project

### Option 2: Using Neon

1. **Create a Neon account**:
   - Go to [neon.tech](https://neon.tech)
   - Sign up for a free account
   - Create a new project

2. **Get your database connection string**:
   - In your Neon dashboard
   - Go to Connection Details
   - Copy the connection string

3. **Deploy to Vercel**:
   - Follow the same steps as for Supabase above

## Heroku Deployment

1. **Create a Heroku account** and install the Heroku CLI

2. **Create a PostgreSQL database**:
   ```bash
   heroku addons:create heroku-postgresql:hobby-dev -a your-app-name
   ```

3. **Set environment variables**:
   ```bash
   heroku config:set FLASK_APP=app.py -a your-app-name
   heroku config:set FLASK_ENV=production -a your-app-name
   ```

4. **Deploy**:
   ```bash
   git push heroku main
   ```

## Other Platforms (AWS, GCP, Azure, etc.)

For other platforms, the process is similar:
1. Set up a PostgreSQL database service
2. Get the connection string
3. Configure it as an environment variable named `DATABASE_URL`
4. Deploy your application

## Environment Variables

Your production deployment requires these environment variables:

- `DATABASE_URL`: PostgreSQL connection string (format: `postgresql://username:password@host:port/database_name`)
- `SECRET_KEY`: A random secret key for session management
- `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`: For email functionality (optional)

## Database Migration

When deploying for the first time or after schema changes:
1. The application will automatically create tables if they don't exist
2. The sample data initialization will run if the database is empty

## Testing Your Deployment

1. After deployment, visit your application URL
2. Register a new account to test the database connection
3. Verify that user data persists between sessions

## Troubleshooting

### Common Issues:

- **Database connection errors**: Verify your `DATABASE_URL` is correctly formatted and accessible
- **Migration errors**: Check that your PostgreSQL version is compatible
- **Permission errors**: Ensure your database user has CREATE and WRITE permissions

### Verifying Database Connection:

You can test your database connection by running:
```python
from app import app, db

with app.app_context():
    # This will attempt to connect to the database
    db.create_all()
    print("Database connection successful!")
```

## Scaling Considerations

- For production use, consider upgrading from free tiers to ensure reliability
- Monitor database connection limits based on your expected user load
- Consider using connection pooling for high-traffic applications