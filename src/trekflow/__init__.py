from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


app = Flask(__name__)
app.config['SECRET_KEY'] = 'fc18f63b887dbe573604eb3c660c5de2'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'


db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' #type: ignore
login_manager.login_message = "You must be logged in to view the treks."
login_manager.login_message_category = "info"

from . import routes
