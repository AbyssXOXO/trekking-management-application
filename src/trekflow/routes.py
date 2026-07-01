from flask import render_template, flash, redirect, url_for, request

from .model import User
from trekflow import app, db, bcrypt
from .forms import RegistrationForms, LoginForms, UpdateProfileForms
from flask_login import login_user, current_user, logout_user, login_required


@app.route("/", methods=['POST', 'GET'])
def home():
    return render_template('home.html', title='Home')

@app.route("/admindashboard", methods=['GET', 'POST'])
def admindashboard():
    return render_template('admin/admindashboard.html', title='Admin')

@app.route("/staffdashboard", methods=['GET', 'POST'])
def staffdashboard():
    return render_template('staff/staffdashboard.html', title='Staff')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForms()   
    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect (next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login unsuccessful. Please check email and password.', 'danger')
    return render_template('auth/login.html', title='Login', form=form)

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForms()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(fullname=form.fullname.data, username=form.username.data, role=form.role.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('login'))
    return render_template('auth/register.html', form=form, title='Register')

@app.route("/logout") 
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/treks", methods=['GET', 'POST'])
@login_required
def treks():
    return render_template('trekker/treks.html', title='Treks')

@app.route("/profile", methods=['POST', 'GET'])
@login_required
def profile():
    form = UpdateProfileForms()
    if form.validate_on_submit():
        if form.pfp.data:
            
        current_user.username = form.username.data
        current_user.fullname = form.fullname.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect (url_for('profile'))
    elif request.method == 'GET':
        form.fullname.data = current_user.fullname  
        form.username.data = current_user.username
        form.email.data = current_user.email 
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('trekker/profile.html', title='Profile', image_file=image_file, form=form)
