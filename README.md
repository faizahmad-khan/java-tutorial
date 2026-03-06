# Java Mastery

A learning management system for Java programming built with Flask and PostgreSQL.

## Features

- User authentication (login, register, password reset)
- Admin panel with full CRUD for courses, lessons, quizzes, assignments, and notes
- Interactive lessons with code editor
- Quiz and assignment system
- Progress tracking and achievements
- Discussion forum
- Deployable to Vercel with Supabase PostgreSQL

## Project Structure

```
app.py                 # Flask application (routes, models, forms)
requirements.txt       # Python dependencies
vercel.json            # Vercel deployment config
.env                   # Environment variables (not committed)
static/
  styles.css           # Main stylesheet
  script.js            # Frontend JavaScript
templates/             # Jinja2 HTML templates
  admin/               # Admin panel templates
LECTURE/               # Sample Java files
```

## Quick Start

```bash
# Clone and enter the project
git clone https://github.com/faizahmad-khan/java-tutorial.git
cd java-tutorial

# Create virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env   # Edit .env with your values

# Initialize the database and run
python app.py
# Visit http://localhost:5000
# Initialize DB: http://localhost:5000/init_db
# Create admin: http://localhost:5000/create_admin?key=YOUR_SETUP_KEY
```

## Environment Variables

| Variable         | Required | Description                                                                                       |
| ---------------- | -------- | ------------------------------------------------------------------------------------------------- |
| `SECRET_KEY`     | Yes      | Session encryption key — generate with `python -c "import secrets; print(secrets.token_hex(16))"` |
| `DATABASE_URL`   | Yes      | PostgreSQL connection string                                                                      |
| `SETUP_KEY`      | Yes      | Secret key for `/create_admin` endpoint                                                           |
| `ADMIN_USERNAME` | Yes      | Admin account username                                                                            |
| `ADMIN_PASSWORD` | Yes      | Admin account password                                                                            |
| `ADMIN_EMAIL`    | Yes      | Admin account email                                                                               |
| `MAIL_SERVER`    | No       | SMTP server (default: smtp.gmail.com)                                                             |
| `MAIL_PORT`      | No       | SMTP port (default: 587)                                                                          |
| `MAIL_USERNAME`  | No       | SMTP username                                                                                     |
| `MAIL_PASSWORD`  | No       | SMTP password                                                                                     |

## Deploying to Vercel

1. Set up a PostgreSQL database (Supabase recommended — SQLite won't work on Vercel)
2. Fork/clone the repo to your GitHub
3. Import the project on [vercel.com](https://vercel.com)
4. Add the environment variables listed above in Vercel project settings
5. Deploy

**Why PostgreSQL?** Vercel serverless functions are ephemeral — SQLite files are lost between requests.

**Why SECRET_KEY?** Without a consistent key, session cookies become invalid across serverless instances, causing login failures.

## Admin Setup

After deploying and initializing the database:

1. Visit `/init_db` to create tables
2. Visit `/create_admin?key=YOUR_SETUP_KEY` to create the admin user
3. Log in — admins are automatically redirected to the admin dashboard

## Tech Stack

- **Backend**: Flask, SQLAlchemy, Flask-Login, Flask-Bcrypt, Flask-Mail, Flask-WTF
- **Database**: PostgreSQL (Supabase) / SQLite (local dev)
- **Frontend**: HTML, CSS, JavaScript, Ace Editor
- **Deployment**: Vercel

## License

MIT
