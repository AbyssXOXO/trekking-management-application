from trekflow import app, bcrypt, db
from trekflow.model import User


with app.app_context():            #for creating admin in User table
    db.create_all()

    admin = User.query.filter_by(role="admin").first()

    if admin:
        print("Admin already exists.")
    else:
        hashed_password = bcrypt.generate_password_hash("admin123").decode("utf-8")

        admin = User()
        admin.fullname = "Administrator"
        admin.username = "admin"
        admin.email = "admin@trekflow.com"
        admin.password = hashed_password
        admin.role = "admin"
        admin.status = "active"

        db.session.add(admin)
        db.session.commit()

        print("Admin created successfully.")


