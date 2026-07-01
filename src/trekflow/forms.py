from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from flask_login import current_user
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Email, ValidationError
from .model import User


class RegistrationForms(FlaskForm):
    fullname = StringField('Full name', validators=[DataRequired(), Length(min=2, max=35)])
    role = SelectField('Who are you?', choices=[('', 'Select an option'), ('user', 'Trekker(User)'), ('staff', 'Trek Flow Staff')], validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Register →')

    def validate_username(self, username):
        user = User.query.filter_by(username = username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')
        
    def validate_email(self, email):
        email = User.query.filter_by(email = email.data).first()
        if email:
            raise ValidationError('That email is already in use. Please try a different one.')

class LoginForms(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Log In →')

class UpdateProfileForms(FlaskForm):
    fullname = StringField('Full name', validators=[DataRequired(), Length(min=2, max=35)])
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    pfp = FileField('Update profile pictures', validators=[FileAllowed(['jpg', 'jpeg', 'png'])])
    submit = SubmitField('Update →')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username = username.data).first()
            if user:
                raise ValidationError('That username is taken. Please choose a different one.')
        
    def validate_email(self, email):
        if email.data != current_user.email:
            email = User.query.filter_by(email = email.data).first()
            if email:
                raise ValidationError('That email is already in use. Please try a different one.')
