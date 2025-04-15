from app import create_app, db
from app.models.user import User

app = create_app()

def main():
    with app.app_context():
        # Print all users with their superuser status
        users = User.query.all()
        
        print("\nCurrent Users:")
        print("=" * 50)
        print(f"{'Username':<20} {'Name':<25} {'Admin':<10} {'Superuser':<10}")
        print("-" * 50)
        
        for user in users:
            print(f"{user.username:<20} {user.name:<25} {str(user.is_admin):<10} {str(user.is_superuser):<10}")
        
        print("\n")
        
        # Ask if user wants to update superuser status
        username = input("Enter username to toggle superuser status (or press Enter to skip): ")
        
        if username:
            user = User.query.filter_by(username=username).first()
            if user:
                user.is_superuser = not user.is_superuser
                db.session.commit()
                print(f"Updated {user.username}: superuser status is now {user.is_superuser}")
            else:
                print(f"User '{username}' not found.")

if __name__ == "__main__":
    main() 