import os
import secrets
from sqlalchemy import or_
from PIL import Image
from flask import render_template, flash, redirect, url_for, request, abort

from .model import User, Trek, Booking, StaffProfile
from trekflow import app, db, bcrypt
from .forms import RegistrationForms, LoginForms, UpdateProfileForms, admin_Staff, AdminTrekForm, admin_Users
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
            elif user.role == "staff" and user.status == "active":
                return redirect(url_for("staffdashboard"))
            elif user.role == "user" and user.status == "active":
                return redirect(url_for("home"))
            else:
                flash('Login unsuccessful, please contact the admin', 'info')
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
        user = User(fullname=form.fullname.data, username=form.username.data, role=form.role.data, status=status, email=form.email.data, password=hashed_password)   #type: ignore
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
    if current_user.role != "admin":
        return redirect(url_for('home'))

    total_treks = Trek.query.count()
    total_users = User.query.filter_by(role='user').count()
    total_staff = User.query.filter_by(role='staff').count()
    total_bookings = Booking.query.count()

    return render_template('admin/admindashboard.html', title='Admin',total_treks=total_treks,total_users=total_users,total_staff=total_staff,total_bookings=total_bookings)

@app.route("/admindashboard/staff", methods=['GET', 'POST'])
@login_required
def admin_staff():
    if current_user.role != "admin":
        return redirect(url_for('home'))
    form = admin_Staff()
    q = request.args.get('q', '').strip()
    staff_results = None
    if q:
        staff_query = User.query.filter_by(role='staff')
        if q.isdigit():
            staff_query = staff_query.filter(db.or_(User.id == int(q), User.username.ilike(f"%{q}%")))
        else:
            staff_query = staff_query.filter(User.username.ilike(f"%{q}%"))
        staff_results = staff_query.all()
    pending_staff = User.query.filter_by(role='staff', status='pending').all()
    approved_staff = User.query.filter_by(role='staff', status='active').all()
    blacklisted_staff = User.query.filter_by(role='staff', status='blacklist').all()
    return render_template('admin/admin_staffs.html', title='Staff', pending_staff=pending_staff, approved_staff=approved_staff, blacklisted_staff=blacklisted_staff, staff_results=staff_results, form=form)

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

@app.route("/admindashboard/newtrek", methods=['GET', 'POST'])
@login_required
def admin_trek():
    if current_user.role != "admin":
        return redirect(url_for('home'))
    form = AdminTrekForm()
    staff_users = User.query.filter_by(role='staff', status='active').all()
    form.assigned_staff.choices = [(0, '-- Select Staff --')] + [(staff.id, staff.fullname) for staff in staff_users] # type: ignore
    return render_template('admin/admin_addtreks.html', title='Add Treks', form=form, assigned_staff=staff_users)

@app.route("/admindashboard/newtrek/save", methods=['POST'])
@login_required
def adding_trek():
    if current_user.role != "admin":
        return redirect(url_for('home'))
    form = AdminTrekForm()
    staff_users = User.query.filter_by(role='staff', status='active').all()
    form.assigned_staff.choices = [(0, '-- Select Staff --')] + [(staff.id, staff.fullname) for staff in staff_users] # type: ignore
    if form.validate_on_submit():
        trek = Trek(trek_name=form.name.data, location=form.location.data, difficulty=form.difficulty.data, duration=form.duration.data, available_slots=form.available_slots.data, total_slots = form.total_slots.data, price = form.price.data, end_date=form.end_date.data, start_date=form.start_date.data, trek_status = form.trek_status.data, assigned_staff_id = form.assigned_staff.data, description = form.description.data) #type:ignore
        db.session.add(trek)
        db.session.commit()
        flash('Trek added successfully', 'success')
        return redirect(url_for('admin_trek'))
    return render_template('admin/admin_addtreks.html', title='Add Treks', form=form)

@app.route("/admindashboard/treks", methods=['GET'])
@login_required
def view_treks():
    if current_user.role != "admin":
        abort(404)
    q = request.args.get('q', '').strip()
    difficulty = request.args.get('difficulty', '').strip()
    status = request.args.get('status', '').strip()
    treks_query = Trek.query
    if q:
        if q.isdigit():
            treks_query = treks_query.filter(db.or_(Trek.trek_id == int(q), Trek.trek_name.ilike(f"%{q}%")))
        else:
            treks_query = treks_query.filter(Trek.trek_name.ilike(f"%{q}%"))
    if difficulty:
        treks_query = treks_query.filter_by(difficulty=difficulty)
    if status:
        treks_query = treks_query.filter_by(trek_status=status)

    treks = treks_query.order_by(Trek.trek_id.desc()).all()
    return render_template('admin/admin_treks.html', title='Treks', treks=treks)

@app.route("/admindashboard/treks/<int:trek_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_treks(trek_id):
    if current_user.role != "admin":
        abort(404)
    trek = Trek.query.get_or_404(trek_id)
    form = AdminTrekForm()
    staff_users = User.query.filter_by(role='staff', status='active').all()
    form.assigned_staff.choices = [(0, '-- Select Staff --')] + [(staff.id, staff.fullname) for staff in staff_users] # type: ignore
    if form.validate_on_submit():
        trek.trek_name = form.name.data
        trek.location = form.location.data
        trek.difficulty = form.difficulty.data
        trek.duration = form.duration.data
        trek.available_slots = form.available_slots.data
        trek.total_slots = form.total_slots.data
        trek.price = form.price.data
        trek.start_date = form.start_date.data
        trek.end_date = form.end_date.data
        trek.trek_status = form.trek_status.data
        trek.assigned_staff_id = form.assigned_staff.data
        trek.description = form.description.data
        db.session.commit()
        flash("Trek updated successfully", "success")
        return redirect(url_for("view_treks"))
    elif request.method == 'GET':
        form.name.data = trek.trek_name
        form.location.data = trek.location
        form.difficulty.data = trek.difficulty
        form.duration.data = trek.duration
        form.available_slots.data = trek.available_slots
        form.total_slots.data = trek.total_slots
        form.price.data = trek.price
        form.start_date.data = trek.start_date
        form.end_date.data = trek.end_date
        form.trek_status.data = trek.trek_status
        form.assigned_staff.data = trek.assigned_staff_id
        form.description.data = trek.description
    return render_template('admin/admin_edittrek.html', title='Edit Trek', trek=trek, form=form)

@app.route("/admindashboard/treks/<int:trek_id>/delete", methods=['POST'])
@login_required
def delete_trek(trek_id):
    if current_user.role != "admin":
        return redirect(url_for('home'))

    trek = Trek.query.get_or_404(trek_id)
    trek.trek_status = 'Closed'
    db.session.commit()

    flash("Trek deleted successfully", "danger")
    return redirect(url_for("view_treks"))

@app.route("/admindashboard/users", methods=['GET', 'POST'])
@login_required
def admin_users():
    if current_user.role != "admin":
        return redirect(url_for('home'))
    form = admin_Users()
    q = request.args.get('q', '').strip()
    user_results = None
    if q:
        user_query = User.query.filter_by(role='user')
        if q.isdigit():
            user_query = user_query.filter(db.or_(User.id == int(q), User.username.ilike(f"%{q}%")))
        else:
            user_query = user_query.filter(User.username.ilike(f"%{q}%"))
        user_results = user_query.all()
    active_user = User.query.filter_by(role='user', status='active').all()
    blacklisted_user = User.query.filter_by(role='user', status='blacklist').all()
    return render_template('admin/admin_users.html', title='Users', active_user=active_user, blacklisted_user=blacklisted_user, user_results=user_results, form=form)

@app.route("/admindashboard/users/<int:user_id>/activate", methods=['POST'])
@login_required
def activate_user(user_id):
    if current_user.role != "admin":
        return redirect(url_for('home'))
    form = admin_Users()
    if form.validate_on_submit():
        user = User.query.get_or_404(user_id)
        if user.role != "user":
            abort(404)
        user.status = "active"
        db.session.commit()
        flash(f'{user.username} has been activated.', 'success')
    return redirect(url_for('admin_users'))

@app.route("/admindashboard/users/<int:user_id>/blacklist", methods=['POST'])
@login_required
def blacklist_user(user_id):
    if current_user.role != "admin":
        return redirect(url_for('home'))
    form = admin_Users()
    if form.validate_on_submit():
        user = User.query.get_or_404(user_id)
        if user.role != "user":
            abort(404)
        user.status = "blacklist"
        db.session.commit()
        flash(f'{user.username} has been blacklisted.', 'danger')
    return redirect(url_for('admin_users'))
