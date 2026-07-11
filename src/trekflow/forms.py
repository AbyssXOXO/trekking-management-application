from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from flask_login import current_user
from wtforms import StringField, PasswordField, SelectField, SubmitField, TextAreaField, IntegerField
from wtforms.fields import DateField
from wtforms.validators import DataRequired, Length, Email, ValidationError, NumberRange, InputRequired
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

class admin_Staff(FlaskForm):
    approve = SubmitField('Approve')
    blacklist = SubmitField('Blacklist')

class AdminTrekForm(FlaskForm):
    name = StringField('Trek name', validators=[DataRequired(), Length(min=2, max=35)])
    location = StringField('Location', validators=[DataRequired(), Length(min=2, max=101)])
    difficulty = SelectField('choose difficulty', choices=[('', '-- Select --'), ('Easy', 'Easy'), ('Moderate', 'Moderate'), ('Hard', 'Hard')], validators=[DataRequired()])
    duration = IntegerField('Duration (days)', validators=[DataRequired(), NumberRange(min=1)])
    total_slots = IntegerField('Total Slots', validators=[DataRequired(), NumberRange(min=1)])
    available_slots = IntegerField('Available Slots', validators=[DataRequired(), NumberRange(min=1)])
    trek_status = SelectField('Trek Status', choices=[('', '--Select--'), ('Open', 'Open'), ('Closed', 'Closed'), ('Started', 'Started'), ('Ongoing', 'Ongoing'), ('Completed', 'Completed')], validators=[DataRequired()])
    price = IntegerField('Price', validators=[DataRequired(), NumberRange(min=1)])
    description = TextAreaField('Description', validators=[DataRequired()])
    start_date = DateField("Start Date", format="%Y-%m-%d", validators=[DataRequired()])
    end_date = DateField("End Date", format="%Y-%m-%d", validators=[DataRequired()])
    assigned_staff = SelectField('Assign Staff', coerce=int, validators=[DataRequired(message='Please select a staff member.')])
    submit = SubmitField('Save')

class CloseTrekForm(FlaskForm):
    close = SubmitField('Close')

class admin_Users(FlaskForm):
    activate = SubmitField('Activate')
    blacklist = SubmitField('Blacklist')

class BookingForm(FlaskForm):
    submit = SubmitField('Book')

class CancelBookingForm(FlaskForm):
    cancel = SubmitField('Cancel')

class ManageTreks(FlaskForm):
    available_slots = IntegerField('Available Slots', validators=[InputRequired(), NumberRange(min=0)])
    trek_status = SelectField('Trek Status', choices=[('Open', 'Open'), ('Closed', 'Closed'), ('Started', 'Started'), ('Ongoing', 'Ongoing'), ('Completed', 'Completed')], validators=[DataRequired()])
    submit = SubmitField('Update Trek')