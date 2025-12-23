from app import app, User


def check_users():
    """Check all users in the database"""
    with app.app_context():
        users = User.query.all()
        print("All users in the database:")
        for user in users:
            print(
                f"ID: {user.id}, Username: {user.username}, "
                f"Email: {user.email}, Role: {user.role}"
            )


if __name__ == "__main__":
    check_users()