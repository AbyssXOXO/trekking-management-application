from flask import render_template, flash, redirect, url_for, request, abort 

from .model import User, Trek, Booking
from trekflow import app, db, bcrypt
from .forms import RegistrationForms, LoginForms, UpdateProfileForms, admin_Staff, AdminTrekForm, admin_Users, BookingForm, CancelBookingForm, CloseTrekForm, ManageTreks
from flask_login import login_user, current_user, logout_user, login_required
from .utils import save_picture


@app.route("/", methods=['GET'])
def home():
    return render_template('home.html', title='Home')

@app.route("/staffdashboard", methods=['GET'])
@login_required
def staffdashboard():
    if current_user.role != "staff":
        return redirect(url_for('home'))
    assigned_treks = Trek.query.filter_by(assigned_staff_id=current_user.id).order_by(Trek.start_date.asc()).all()
    open_treks = sum(1 for trek in assigned_treks if trek.trek_status == "Open")
    bookings = (Booking.query.join(Trek).filter(Trek.assigned_staff_id == current_user.id, Booking.booking_status == "Booked").all())
    trekkers = [booking.trekker for booking in bookings]
    return render_template('staff/staffdashboard.html', title='Staff', assigned_treks=assigned_treks, open_treks=open_treks, trekkers=trekkers)

@app.route("/staffdashboard/treks", methods=['GET'])
@login_required
def stafftreks():                
    if current_user.role != "staff":
        return redirect(url_for('home'))
    form = ManageTreks()
    treks = Trek.query.filter_by(assigned_staff_id=current_user.id).order_by(Trek.start_date.asc()).all()
    return render_template('staff/stafftreks.html', title='Assigned Treks', treks=treks, form=form)

@app.route("/staffdashboard/<int:trek_id>/manage", methods=['GET', 'POST'])
@login_required
def staffmanagetreks(trek_id):                
    if current_user.role != "staff":
        return redirect(url_for('home'))
    form = ManageTreks()
    trek = Trek.query.filter_by(trek_id=trek_id, assigned_staff_id=current_user.id).first_or_404()
    bookings = Booking.query.filter_by(trek_id=trek.trek_id, booking_status="Booked").order_by(Booking.booking_date.asc()).all()
    if form.validate_on_submit():
        if form.available_slots.data > trek.total_slots:
            flash("Available slots cannot be more than total slots", "warning")
            return redirect(url_for('staffmanagetreks', trek_id=trek.trek_id))
        trek.available_slots = form.available_slots.data
        trek.trek_status = form.trek_status.data
        db.session.commit()
        flash("Trek updated successfully.", "success")
        return redirect(url_for("staffmanagetreks", trek_id=trek.trek_id))
    elif request.method == "GET":
        form.available_slots.data = trek.available_slots
        form.trek_status.data = trek.trek_status
    return render_template('staff/manage_treks.html', title='Manage Trek', trek=trek, bookings=bookings, form=form)

@app.route("/staffdashboard/profile", methods=['GET', 'POST'])
@login_required
def staffprofile():                
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
        return redirect (url_for('staffprofile'))
    elif request.method == 'GET':
        form.fullname.data = current_user.fullname  
        form.username.data = current_user.username
        form.email.data = current_user.email 
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('staff/profile.html', title='Profile', image_file=image_file, form=form)


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
            flash('Login successful.', 'success')
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
    if current_user.role != 'user':
        return redirect(url_for('home'))
    form = BookingForm()
    difficulty = request.args.get("difficulty", "").strip()
    location = request.args.get("location", "").strip()
    treks_query = Trek.query.filter(Trek.trek_status.in_(["Open", "Closed", "Started", "Ongoing"]))
    if difficulty:
        treks_query = treks_query.filter_by(difficulty=difficulty)
    if location:
        treks_query = treks_query.filter_by(location=location)
    treks = treks_query.order_by(Trek.start_date.asc()).all()
    locations = [row[0] for row in db.session.query(Trek.location).filter_by(trek_status="Open").distinct().order_by(Trek.location.asc()).all()]
    return render_template('trekker/treks.html', title='Treks', form=form, treks=treks, locations=locations, selected_difficulty = difficulty, selected_location = location)

@app.route("/treks/<int:trek_id>/book", methods=['POST'])
@login_required
def book_trek(trek_id):
    if current_user.role != "user":
        return redirect(url_for('home'))
    form = BookingForm()
    if form.validate_on_submit():
        trek = Trek.query.get_or_404(trek_id)
        if trek.trek_status != "Open":
            flash("This trek is not open for booking.", "warning")
            return redirect(url_for("treks"))
        if trek.available_slots <= 0:
            flash("No slots available for this trek.", "danger")
            return redirect(url_for("treks"))
        existing_booking = Booking.query.filter_by(trekker_id=current_user.id, trek_id=trek.trek_id, booking_status ="Booked").first()
        if existing_booking:
            flash("You have already booked this trek.", "info")
            return redirect(url_for('treks'))
        booking = Booking(trekker_id=current_user.id, trek_id=trek.trek_id, booking_status="Booked")     #type: ignore
        trek.available_slots -= 1
        db.session.add(booking)
        db.session.commit()
        flash("Trek booked successfully!", "success")
    return redirect(url_for('treks'))

@app.route("/booking", methods=['GET'])
@login_required
def mybooking():
    if current_user.role != "user":
        return redirect(url_for('home'))
    bookings = (Booking.query.join(Trek).filter(Booking.trekker_id==current_user.id, Booking.booking_status=="Booked", db.or_(Trek.trek_status=="Open", Trek.trek_status=="Closed", Trek.trek_status=="Started", Trek.trek_status=="Ongoing")).all())
    return render_template("trekker/mybooking.html", title="My Bookings", bookings=bookings)

@app.route("/booking/<int:booking_id>/details", methods=['GET'])
@login_required
def viewbooking(booking_id):
    if current_user.role != "user":
        return redirect(url_for('home'))
    booking = Booking.query.filter_by(booking_id=booking_id, trekker_id=current_user.id).first_or_404()
    return render_template('trekker/viewbooking.html', title='Booking Details', booking=booking)

@app.route("/history", methods=['GET'])
@login_required
def history():
    if current_user.role != "user":
        return redirect(url_for('home'))
    bookings = (Booking.query.join(Trek).filter(Booking.trekker_id==current_user.id, Booking.booking_status=="Booked", Trek.trek_status=="Completed").all())
    return render_template("trekker/bookinghistory.html", title="History", bookings=bookings)

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
    form = CloseTrekForm()
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
    return render_template('admin/admin_treks.html', title='Treks', treks=treks, form=form)

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
    form = CloseTrekForm()
    if form.validate_on_submit():
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

@app.route("/admindashboard/bookings", methods=['GET'])
@login_required
def booking_admin():
    if current_user.role != "admin":
        return abort(404)
    form = CancelBookingForm()
    bookings = Booking.query.order_by(Booking.booking_date.desc()).all()
    return render_template("admin/admin_booking.html", title="Bookings", bookings=bookings, form=form)

@app.route("/admindashboard/bookings/<int:booking_id>/cancel", methods=["POST"])
@login_required
def admin_cancel_booking(booking_id):
    if current_user.role != "admin":
        abort(404)
    form = CancelBookingForm()
    if form.validate_on_submit():
        booking = Booking.query.get_or_404(booking_id)
        if booking.booking_status == "Cancelled":
            flash("Booking is already cancelled.", "info")
            return redirect(url_for("booking_admin"))
        booking.booking_status = "Cancelled"
        booking.trek.available_slots += 1
        db.session.commit()
        flash("Booking cancelled successfully.", "success")
    return redirect(url_for("booking_admin"))
