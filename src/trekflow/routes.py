import os
import secrets
from PIL import Image
from flask import render_template, flash, redirect, url_for, request, abort

from .model import User
from trekflow import app, db, bcrypt
from .forms import RegistrationForms, LoginForms, UpdateProfileForms, admin_Staff
from flask_login import login_user, current_user, logout_user, login_required


@app.route("/", methods=['POST', 'GET'])
def home():
    return render_template('home.html', title='Home')

@app.route("/staffdashboard", methods=['GET', 'POST'])
@login_required
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
            if user.role == "staff" and user.status != "active":
                flash('Your staff account is waiting for admin approval.', 'warning')
                return redirect(url_for('login'))
            login_user(user)
            next_page = request.args.get('next')
            if next_page:
                return redirect (next_page) if next_page else redirect(url_for('home'))
            if user.role == "admin":
                return redirect(url_for("admindashboard"))
            elif user.role == "staff":
                return redirect(url_for("staffdashboard"))
            else:
                return redirect(url_for("home"))
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
        status = 'pending' if form.role.data == 'staff' else 'active'
        user = User(fullname=form.fullname.data, username=form.username.data, role=form.role.data, status=status, email=form.email.data, password=hashed_password)
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

def save_picture(form_picture): #for getting the ext and file name for pfp
    random_hex = secrets.token_hex(16)
    _, f_ext = os.path.splitext(form_picture.filename)
    pfp_fn = random_hex + f_ext 
    pfp_path = os.path.join(app.root_path, 'static/profile_pics', pfp_fn)

    output_size = (120, 120)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(pfp_path)

    return pfp_fn #to return the name to be saved in db

@app.route("/profile", methods=['POST', 'GET'])
@login_required
def profile():
    form = UpdateProfileForms()
    if form.validate_on_submit():
        if form.pfp.data:
            pfp_file = save_picture(form.pfp.data)
            current_user.image_file = pfp_file
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

@app.route("/admindashboard", methods=['GET', 'POST'])
@login_required
def admindashboard():
    return render_template('admin/admindashboard.html', title='Admin')

@app.route("/admindashboard/staff", methods=['GET', 'POST'])
@login_required
def admin_staff():
    if current_user.role != "admin":
        return redirect(url_for('home'))
    form = admin_Staff()
    pending_staff = User.query.filter_by(role='staff', status='pending').all()
    approved_staff = User.query.filter_by(role='staff', status='active').all()
    blacklisted_staff = User.query.filter_by(role='staff', status='blacklist').all()
    return render_template('admin/admin_staffs.html', title='Staff', pending_staff=pending_staff, approved_staff=approved_staff, blacklisted_staff=blacklisted_staff, form=form)

@app.route("/admindashboard/staff/<int:user_id>/approve", methods=['POST'])
@login_required
def approve_staff(user_id):
    if current_user.role != "admin":
        return redirect(url_for('home'))
    form = admin_Staff()
    if form.validate_on_submit():
        staff = User.query.get_or_404(user_id)
        if staff.role != "staff":
            abort(404)
        staff.status = "active"
        db.session.commit()
        flash(f'{staff.username} has been approved.', 'success')
    return redirect(url_for('admin_staff'))

@app.route("/admindashboard/staff/<int:user_id>/blacklist", methods=['POST'])
@login_required
def blacklist_staff(user_id):
    if current_user.role != "admin":
        return redirect(url_for('home'))
    form = admin_Staff()
    if form.validate_on_submit():
        staff = User.query.get_or_404(user_id)
        if staff.role != "staff":
            abort(404)
        staff.status = "blacklist"
        db.session.commit()
        flash(f'{staff.username} has been blacklisted.', 'danger')
    return redirect(url_for('admin_staff'))
