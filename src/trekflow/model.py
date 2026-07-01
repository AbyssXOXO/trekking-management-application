from trekflow import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(35), nullable=False)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.png')
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(8), nullable=False)

    def __init__(self, fullname, username, email, password, role):
        self.fullname = fullname
        self.username = username
        self.email = email
        self.password = password
        self.role = role

    def __repr__(self):
        return f"user('{self.id}', '{self.fullname}', '{self.username}', '{self.image_file}', '{self.role}')"
