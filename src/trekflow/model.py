from trekflow import db, login_manager
from flask_login import UserMixin

from datetime import date

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(35), nullable=False)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(120), nullable=False, default='default.png')
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum("admin", "staff", "user"), nullable=False)
    status = db.Column(db.Enum("active", "pending", "blacklist"), nullable=False)
    created_date = db.Column(db.Date, nullable=False, default=date.today)

    def __repr__(self):
        return f"user('{self.id}', '{self.fullname}', '{self.username}', '{self.image_file}', '{self.role}', '{self.status}', '{self.created_date}')"


class StaffProfile(db.Model):
    __tablename__ = "staff_profile"
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    contact = db.Column(db.String(15), unique=True)
    address = db.Column(db.String(200))
    bio = db.Column(db.Text)

    user = db.relationship("User", backref=db.backref("staff_profile", uselist=False))

    def __repr__(self):
        return f"staff('{self.id}', '{self.user_id}', '{self.address}', '{self.bio}', '{self.contact}')"


class Trek(db.Model):
    __tablename__ = "trek"
    trek_id = db.Column(db.Integer, primary_key=True, nullable=False)
    trek_name = db.Column(db.String(35), nullable=False)
    location = db.Column(db.String(101), nullable=False)
    difficulty = db.Column(db.Enum("Easy", "Moderate", "Hard"), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    total_slots = db.Column(db.Integer, nullable=False)
    available_slots = db.Column(db.Integer, nullable=False)
    assigned_staff_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    trek_status = db.Column(db.Enum("Open", "Closed","Started", "Ongoing", "Completed"), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    staff = db.relationship("User", backref=db.backref("treks"))

    def __repr__(self):
        return f"trek('{self.trek_id}', '{self.trek_name}', '{self.location}', '{self.difficulty}', '{self.duration}', '{self.available_slots}', '{self.total_slots}', '{self.assigned_staff_id}', '{self.trek_status}', '{self.price}', '{self.description}', '{self.start_date}', '{self.end_date}')"


class Booking(db.Model):
    __tablename__ = "booking"
    booking_id = db.Column(db.Integer, primary_key=True, nullable=False)
    trekker_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey('trek.trek_id'), nullable=False)
    booking_date = db.Column(db.Date, nullable=False, default=date.today)
    booking_status = db.Column(db.Enum("Booked", "Cancelled"), nullable=False)

    trekker = db.relationship("User", backref=db.backref("bookings"))
    trek = db.relationship("Trek", backref=db.backref("bookings"))

    def __repr__(self):
        return f"booking('{self.booking_id}', '{self.trekker_id}', '{self.trek_id}', '{self.booking_status}')"
