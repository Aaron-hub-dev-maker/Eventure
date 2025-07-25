from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash, abort
from pymongo import MongoClient
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
import os
from werkzeug.utils import secure_filename
import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import qrcode
import base64
from email.mime.image import MIMEImage
import requests
import time

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Change this in production

UPLOAD_FOLDER = os.path.join('static', 'images')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["events"]
events_collection = db["parties"]
users_collection = db["users"]

# Add bookings collection
bookings_collection = db["bookings"]

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_doc):
        self.id = str(user_doc['_id'])
        self.username = user_doc['username']
        self.email = user_doc['email']
    @staticmethod
    def get(user_id):
        user_doc = users_collection.find_one({'_id': ObjectId(user_id)})
        if user_doc:
            return User(user_doc)
        return None

@login_manager.user_loader
def load_user(user_id):
    try:
        user_doc = users_collection.find_one({'_id': ObjectId(user_id)})
        if user_doc:
            return User(user_doc)
    except Exception:
        return None
    return None

@app.context_processor
def inject_user():
    return dict(current_user=current_user)

def send_otp_email(recipient_email, otp):
    sender_email = 'eventure39@gmail.com'  # Replace with your email
    sender_password = 'zcmz dyxu fzeg jwug'  # Replace with your email password or app password
    subject = 'Your OTP Verification Code'
    body = f'Your OTP code is: {otp}'

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Error sending OTP email: {e}")
        return False

def send_ticket_email(recipient_email, event, booking, qr_path):
    sender_email = 'eventure39@gmail.com'
    sender_password = 'zcmz dyxu fzeg jwug'
    subject = f"Your Ticket for {event.get('Name', 'Event')}"

    # HTML body (matches ticket.html style)
    body = f'''
    <html>
    <body style="background:#eaf6f3;margin:0;padding:0;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#eaf6f3;padding:32px 0;">
      <tr>
        <td align="center">
          <table cellpadding="0" cellspacing="0" border="0" style="max-width:420px;width:100%;background:#fff;border-radius:18px;box-shadow:0 4px 16px rgba(0,0,0,0.10);overflow:hidden;">
            <tr>
              <td style="background:#4CAF50;padding:24px 0 12px 0;text-align:center;color:#fff;font-size:2em;font-weight:700;letter-spacing:1px;border-top-left-radius:18px;border-top-right-radius:18px;">
                <div style="font-size:2.2em;margin-bottom:8px;"><i class="fa-solid fa-ticket"></i></div>
                Your Ticket
              </td>
            </tr>
            <tr>
              <td style="padding:24px 32px 8px 32px;">
                <table width="100%" cellpadding="0" cellspacing="0" border="0" style="font-size:1.08em;">
                  <tr><td style="padding:6px 0;"><strong style="color:#4CAF50;">Event:</strong> {event.get('Name', '')}</td></tr>
                  <tr><td style="padding:6px 0;"><strong style="color:#4CAF50;">Date:</strong> {event.get('Date', '')}</td></tr>
                  <tr><td style="padding:6px 0;"><strong style="color:#4CAF50;">Place:</strong> {event.get('Place', '')}</td></tr>
                  <tr><td style="padding:6px 0;"><strong style="color:#4CAF50;">Category:</strong> {event.get('Category', '')}</td></tr>
                  <tr><td style="padding:6px 0;"><strong style="color:#4CAF50;">Landmark:</strong> {event.get('Checkpoint', '')}</td></tr>
                  <tr><td style="padding:6px 0;"><strong style="color:#4CAF50;">Distance:</strong> {event.get('Distance', '')} km</td></tr>
                  <tr><td style="padding:6px 0;"><strong style="color:#4CAF50;">Number of Tickets:</strong> {booking.get('num_tickets', 1)}</td></tr>
                  <tr><td style="padding:6px 0;"><strong style="color:#4CAF50;">Booking ID:</strong> {booking.get('_id', '')}</td></tr>
                </table>
              </td>
            </tr>
            <tr>
              <td align="center" style="padding:18px 0 18px 0;">
                <img src="cid:qrcodeimg" alt="QR Code" style="width:160px;height:160px;border-radius:12px;background:#f7f7f7;padding:8px;box-shadow:0 2px 8px rgba(0,0,0,0.10);">
              </td>
            </tr>
            <tr>
              <td style="background:#f7f7f7;padding:14px 0;text-align:center;color:#888;font-size:1.05em;border-bottom-left-radius:18px;border-bottom-right-radius:18px;">
                Enjoy your event!<br>&copy; 2024 Eventure
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
    </body>
    </html>
    '''

    msg = MIMEMultipart('related')
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    msg_alt = MIMEMultipart('alternative')
    msg.attach(msg_alt)
    msg_alt.attach(MIMEText(body, 'html'))

    # Attach QR code as inline image
    with open(qr_path, 'rb') as f:
        img = MIMEImage(f.read(), _subtype="png")
        img.add_header('Content-ID', '<qrcodeimg>')
        img.add_header('Content-Disposition', 'inline', filename=os.path.basename(qr_path))
        msg.attach(img)

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        print('Ticket email sent!')
    except Exception as e:
        print(f'Error sending ticket email: {e}')

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form["full_name"]
        username = request.form["username"]
        email = request.form["email"]
        phone = request.form["phone"]
        city = request.form["city"]
        password = request.form["password"]
        recaptcha_response = request.form.get('g-recaptcha-response')
        # Verify reCAPTCHA
        secret_key = '6LcVrIwrAAAAAMTL7sV8GdJmYRZo22d4KwESpuOi'
        recaptcha_verify_url = 'https://www.google.com/recaptcha/api/siteverify'
        data = {'secret': secret_key, 'response': recaptcha_response}
        recaptcha_result = requests.post(recaptcha_verify_url, data=data).json()
        if not recaptcha_result.get('success'):
            flash("reCAPTCHA verification failed. Please try again.", "danger")
            return render_template("register.html")
        if users_collection.find_one({"$or": [{"username": username}, {"email": email}]}):
            flash("Username or email already exists.", "danger")
            return render_template("register.html")
        # Generate OTP
        otp = str(random.randint(100000, 999999))
        # Store registration data and OTP in session
        session['pending_registration'] = {
            'full_name': full_name,
            'username': username,
            'email': email,
            'phone': phone,
            'city': city,
            'password': generate_password_hash(password),
            'otp': otp
        }
        # Send OTP email
        if send_otp_email(email, otp):
            flash("An OTP has been sent to your email. Please verify.", "info")
            return redirect(url_for("verify_otp"))
        else:
            flash("Failed to send OTP email. Please try again.", "danger")
            return render_template("register.html")
    return render_template("register.html")

@app.route("/verify_otp", methods=["GET", "POST"])
def verify_otp():
    if 'pending_registration' not in session:
        flash("No registration in progress.", "danger")
        return redirect(url_for("register"))
    if request.method == "POST":
        user_otp = request.form.get('otp')
        reg_data = session['pending_registration']
        if user_otp == reg_data['otp']:
            # Save user to DB
            user_doc = {
                "full_name": reg_data['full_name'],
                "username": reg_data['username'],
                "email": reg_data['email'],
                "phone": reg_data['phone'],
                "city": reg_data['city'],
                "password": reg_data['password']
            }
            users_collection.insert_one(user_doc)
            session.pop('pending_registration')
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login"))
        else:
            flash("Invalid OTP. Please try again.", "danger")
    return render_template("verify_otp.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username_or_email = request.form["username"]
        password = request.form["password"]
        user_doc = users_collection.find_one({"$or": [{"username": username_or_email}, {"email": username_or_email}]})
        if user_doc and check_password_hash(user_doc["password"], password):
            # 2FA: Generate OTP, send to email, store in session
            otp = str(random.randint(100000, 999999))
            session['2fa_user_id'] = str(user_doc['_id'])
            session['2fa_otp'] = otp
            session['2fa_email'] = user_doc['email']
            if send_otp_email(user_doc['email'], otp):
                flash("A verification code has been sent to your email. Please enter it to continue.", "info")
                return redirect(url_for("verify_2fa"))
            else:
                flash("Failed to send verification code. Please try again.", "danger")
        else:
            flash("Invalid credentials.", "danger")
    return render_template("login.html")

@app.route('/verify_2fa', methods=['GET', 'POST'])
def verify_2fa():
    if '2fa_user_id' not in session or '2fa_otp' not in session:
        flash('No 2FA verification in progress. Please log in again.', 'danger')
        return redirect(url_for('login'))
    cooldown = 30
    now = int(time.time())
    last_resend = session.get('2fa_last_resend', 0)
    seconds_left = max(0, cooldown - (now - last_resend))
    if request.method == 'POST':
        if 'resend_otp' in request.form:
            if seconds_left > 0:
                flash(f'Please wait {seconds_left} seconds before resending the code.', 'danger')
            else:
                otp = str(random.randint(100000, 999999))
                session['2fa_otp'] = otp
                session['2fa_last_resend'] = now
                email = session.get('2fa_email', '')
                if send_otp_email(email, otp):
                    flash('A new verification code has been sent to your email.', 'info')
                else:
                    flash('Failed to send verification code. Please try again.', 'danger')
        else:
            user_otp = request.form.get('otp')
            if user_otp == session['2fa_otp']:
                user = User.get(session['2fa_user_id'])
                if user:
                    login_user(user)
                    # Clean up session
                    session.pop('2fa_user_id')
                    session.pop('2fa_otp')
                    session.pop('2fa_email')
                    session.pop('2fa_last_resend', None)
                    flash('Logged in successfully!', 'success')
                    return redirect(url_for('event_listings'))
                else:
                    flash('User not found.', 'danger')
            else:
                flash('Invalid verification code. Please try again.', 'danger')
    email = session.get('2fa_email', '')
    # Recalculate seconds_left for GET or after POST
    now = int(time.time())
    last_resend = session.get('2fa_last_resend', 0)
    seconds_left = max(0, cooldown - (now - last_resend))
    return render_template('verify_2fa.html', email=email, seconds_left=seconds_left)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "success")
    return redirect(url_for("event_listings"))

@app.route("/", methods=["GET", "POST"])
@login_required
def event_listings():
    distance = request.args.get("distance", type=int)
    place = request.args.get("place")
    search_query = request.args.get("search", "").strip()
    selected_date = request.args.get("date")
    selected_time = request.args.get("time")
    selected_category = request.args.get("category")

    filter_criteria = {}
    if search_query:
        filter_criteria["Name"] = {"$regex": search_query, "$options": "i"}
    if distance:
        filter_criteria["Distance"] = {"$lte": distance}
    if place:
        filter_criteria["Place"] = place
    if selected_category:
        filter_criteria["Category"] = selected_category
    if selected_date:
        from datetime import datetime, time as dt_time
        try:
            date_obj = datetime.strptime(selected_date, "%Y-%m-%d")
            if selected_time:
                time_obj = datetime.strptime(selected_time, "%H:%M").time()
                dt_start = datetime.combine(date_obj, time_obj)
                filter_criteria["Date"] = {"$gte": dt_start}
            else:
                dt_start = datetime.combine(date_obj, dt_time.min)
                dt_end = datetime.combine(date_obj, dt_time.max)
                filter_criteria["Date"] = {"$gte": dt_start, "$lte": dt_end}
        except Exception as e:
            print("Error parsing date/time filter:", e)
    try:
        events = list(events_collection.find(filter_criteria))
        for event in events:
            event['_id'] = str(event['_id'])
        selected_place = request.args.get("place")
        selected_distance = request.args.get("distance", type=int)
        return render_template("index.html", events=events, selected_place=selected_place, selected_distance=selected_distance, search_query=search_query, selected_date=selected_date, selected_time=selected_time, selected_category=selected_category)
    except Exception as e:
        import traceback
        print("Error retrieving events:", e)
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Error fetching events'}), 500

@app.route("/host", methods=["GET", "POST"])
@login_required
def host():
    if request.method == "POST":
        try:
            name = request.form["name"]
            date = request.form["date"]
            time = request.form["time"]
            place = request.form["place"]
            distance = int(request.form["distance"])
            category = request.form["category"]
            checkpoint = request.form["checkpoint"]
            location = request.form.get('location', '').strip() or None
            event_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
            image_filename = None
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filename = f"{name.replace(' ', '_')}_{filename}"
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    image_filename = filename
            # Store event details and OTP in session, send OTP
            otp = str(random.randint(100000, 999999))
            session['pending_event'] = {
                "Name": name,
                "Date": date,
                "Time": time,
                "Place": place,
                "Distance": distance,
                "Category": category,
                "Checkpoint": checkpoint,
                "hosted_by": current_user.username,
                "Location": location,
                "image_filename": image_filename,
                "otp": otp
            }
            user_doc = users_collection.find_one({'_id': ObjectId(current_user.id)})
            if user_doc and user_doc.get('email'):
                if send_otp_email(user_doc['email'], otp):
                    flash("A verification code has been sent to your email. Please enter it to continue.", "info")
                    return redirect(url_for("verify_host_otp"))
                else:
                    flash("Failed to send verification code. Please try again.", "danger")
                    return render_template("host.html")
            else:
                flash("Could not find your email address.", "danger")
                return render_template("host.html")
        except Exception as e:
            print(f"Error preparing event: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
    return render_template("host.html")

@app.route('/verify_host_otp', methods=['GET', 'POST'])
@login_required
def verify_host_otp():
    if 'pending_event' not in session:
        flash("No event submission in progress.", "danger")
        return redirect(url_for("host"))
    event_data = session['pending_event']
    cooldown = 30
    now = int(time.time())
    last_resend = session.get('host_otp_last_resend', 0)
    seconds_left = max(0, cooldown - (now - last_resend))
    if request.method == 'POST':
        if 'resend_otp' in request.form:
            if seconds_left > 0:
                flash(f'Please wait {seconds_left} seconds before resending the code.', 'danger')
            else:
                otp = str(random.randint(100000, 999999))
                session['pending_event']['otp'] = otp
                session['host_otp_last_resend'] = now
                user_doc = users_collection.find_one({'_id': ObjectId(current_user.id)})
                if user_doc and user_doc.get('email'):
                    if send_otp_email(user_doc['email'], otp):
                        flash('A new verification code has been sent to your email.', 'info')
                    else:
                        flash('Failed to send verification code. Please try again.', 'danger')
        else:
            user_otp = request.form.get('otp')
            if user_otp == event_data['otp']:
                # Save event to DB
                try:
                    event_datetime = datetime.strptime(f"{event_data['Date']} {event_data['Time']}", "%Y-%m-%d %H:%M")
                    event = {
                        "Name": event_data['Name'],
                        "Date": event_datetime,
                        "Place": event_data['Place'],
                        "Distance": event_data['Distance'],
                        "Category": event_data['Category'],
                        "Checkpoint": event_data['Checkpoint'],
                        "hosted_by": event_data['hosted_by'],
                        "Location": event_data['Location']
                    }
                    if event_data['image_filename']:
                        event['image'] = event_data['image_filename']
                    events_collection.insert_one(event)
                    session.pop('pending_event')
                    session.pop('host_otp_last_resend', None)
                    flash('Event hosted successfully and added to the list!', 'success')
                    return redirect(url_for('event_listings', success=1))
                except Exception as e:
                    flash(f'Error saving event: {e}', 'danger')
            else:
                flash('Invalid verification code. Please try again.', 'danger')
    # Recalculate seconds_left for GET or after POST
    now = int(time.time())
    last_resend = session.get('host_otp_last_resend', 0)
    seconds_left = max(0, cooldown - (now - last_resend))
    return render_template('verify_host_otp.html', seconds_left=seconds_left)

@app.route("/FAQ")
def faq():
    return render_template("FAQ.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        message = request.form.get("message")
        user_email = request.form.get("email")
        recaptcha_response = request.form.get('g-recaptcha-response')
        # Verify reCAPTCHA
        secret_key = '6LdhQ4orAAAAAJDmhEo2Evn1e_AjqyV_LwGRpH7V'
        recaptcha_verify_url = 'https://www.google.com/recaptcha/api/siteverify'
        data = {'secret': secret_key, 'response': recaptcha_response}
        recaptcha_result = requests.post(recaptcha_verify_url, data=data).json()
        if not recaptcha_result.get('success'):
            flash("reCAPTCHA verification failed. Please try again.", "danger")
            return render_template("contact.html")
        admin_email = 'eventure39@gmail.com'
        subject = f"Contact Form Message from {name}"
        body = f"You have received a new message from the contact form.\n\nName: {name}"
        if user_email:
            body += f"\nEmail: {user_email}"
        body += f"\nMessage: {message}"
        sender_email = 'eventure39@gmail.com'
        sender_password = 'zcmz dyxu fzeg jwug'
        try:
            import smtplib
            from email.mime.text import MIMEText
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = sender_email
            msg['To'] = admin_email
            if user_email:
                msg['Reply-To'] = user_email
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, admin_email, msg.as_string())
            print('Contact form message sent to admin!')
        except Exception as e:
            print(f'Error sending contact form message: {e}')
        return redirect(url_for("confirmation"))
    return render_template("contact.html")

@app.route("/confirmation")
def confirmation():
    return render_template("confirmation.html")

@app.route('/confirmation2')
def confirmation2():
    return render_template('confirmation.html')

@app.route("/referrals")
def referral():
    return render_template('referrals.html')

@app.route("/upload_event_image/<event_id>", methods=["POST"])
@login_required
def upload_event_image(event_id):
    if 'image' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('event_listings'))
    file = request.files['image']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('event_listings'))
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Make filename unique by prefixing with event_id
        filename = f"{event_id}_{filename}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        # Update event in MongoDB
        events_collection.update_one({'_id': ObjectId(event_id)}, {'$set': {'image': filename}})
        flash('Event image updated!', 'success')
    else:
        flash('Invalid file type. Allowed: png, jpg, jpeg, gif', 'danger')
    return redirect(url_for('event_listings'))

@app.route('/event/<event_id>')
def event_detail(event_id):
    event = events_collection.find_one({'_id': ObjectId(event_id)})
    if not event:
        abort(404)
    return render_template('event_detail.html', event=event)

# Edit event route
@app.route('/edit_event/<event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    event = events_collection.find_one({'_id': ObjectId(event_id)})
    if not event:
        abort(404)
    # Allow host or admin
    is_admin = (current_user.username == 'Admin' and current_user.email == 'eventure39@gmail.com')
    if event.get('hosted_by') != current_user.username and not is_admin:
        flash('You are not authorized to edit this event.', 'danger')
        return redirect(url_for('event_listings'))
    if request.method == 'POST':
        try:
            name = request.form['name']
            date = request.form['date']
            time = request.form['time']
            place = request.form['place']
            distance = int(request.form['distance'])
            category = request.form['category']
            checkpoint = request.form['checkpoint']
            # Admin can update Location
            if is_admin:
                location = request.form.get('location', '').strip() or None
            else:
                location = event.get('Location', None)
            event_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
            update_fields = {
                'Name': name,
                'Date': event_datetime,
                'Place': place,
                'Distance': distance,
                'Category': category,
                'Checkpoint': checkpoint,
                'Location': location
            }
            # Handle image update
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filename = f"{name.replace(' ', '_')}_{filename}"
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    update_fields['image'] = filename
            events_collection.update_one({'_id': ObjectId(event_id)}, {'$set': update_fields})
            flash('Event updated successfully!', 'success')
            return redirect(url_for('event_detail', event_id=event_id))
        except Exception as e:
            flash(f'Error updating event: {e}', 'danger')
    # Pre-fill form with event data
    return render_template('edit_event.html', event=event)

# Delete event route
@app.route('/delete_event/<event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    event = events_collection.find_one({'_id': ObjectId(event_id)})
    if not event:
        abort(404)
    # Allow host or admin
    is_admin = (current_user.username == 'Admin' and current_user.email == 'eventure39@gmail.com')
    if event.get('hosted_by') != current_user.username and not is_admin:
        flash('You are not authorized to delete this event.', 'danger')
        return redirect(url_for('event_listings'))
    try:
        events_collection.delete_one({'_id': ObjectId(event_id)})
        flash('Event deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting event: {e}', 'danger')
    return redirect(url_for('event_listings'))

@app.route('/book_ticket/<event_id>', methods=['POST'])
@login_required
def book_ticket(event_id):
    event = events_collection.find_one({'_id': ObjectId(event_id)})
    if not event:
        abort(404)
    # Get number of tickets from form
    num_tickets = int(request.form.get('num_tickets', 1))
    # Create booking
    booking = {
        'user_id': current_user.id,
        'event_id': str(event['_id']),
        'timestamp': datetime.now(),
        'status': 'booked',
        'num_tickets': num_tickets
    }
    booking_id = bookings_collection.insert_one(booking).inserted_id

    # Generate QR code with ticket details
    qr_data = {
        'booking_id': str(booking_id),
        'user_id': current_user.id,
        'event_id': str(event['_id']),
        'event_name': event.get('Name', ''),
        'date': str(event.get('Date', '')),
        'place': event.get('Place', ''),
        'category': event.get('Category', ''),
        'checkpoint': event.get('Checkpoint', ''),
        'distance': event.get('Distance', ''),
        'num_tickets': num_tickets
    }
    qr = qrcode.make(str(qr_data))
    qr_filename = f'ticket_{booking_id}.png'
    qr_path = os.path.join(app.config['UPLOAD_FOLDER'], qr_filename)
    qr.save(qr_path)

    # Save QR filename in booking
    bookings_collection.update_one({'_id': booking_id}, {'$set': {'qr_filename': qr_filename}})

    # Send ticket email to user
    user_doc = users_collection.find_one({'_id': ObjectId(current_user.id)})
    if user_doc and user_doc.get('email'):
        # Add booking _id for email body
        booking['_id'] = booking_id
        send_ticket_email(user_doc['email'], event, booking, qr_path)

    return redirect(url_for('ticket', booking_id=booking_id))

@app.route('/ticket/<booking_id>')
@login_required
def ticket(booking_id):
    booking = bookings_collection.find_one({'_id': ObjectId(booking_id)})
    if not booking or booking['user_id'] != current_user.id:
        abort(404)
    event = events_collection.find_one({'_id': ObjectId(booking['event_id'])})
    qr_filename = booking.get('qr_filename')
    return render_template('ticket.html', booking=booking, event=event, qr_filename=qr_filename)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_doc = users_collection.find_one({'_id': ObjectId(current_user.id)})
    if not user_doc:
        flash('User not found.', 'danger')
        return redirect(url_for('event_listings'))
    password_error = None
    if request.method == 'POST':
        if 'change_password' in request.form:
            # Handle password change
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')
            if not check_password_hash(user_doc['password'], current_password):
                password_error = 'Current password is incorrect.'
            elif new_password != confirm_password:
                password_error = 'New passwords do not match.'
            elif len(new_password) < 6:
                password_error = 'New password must be at least 6 characters.'
            else:
                users_collection.update_one({'_id': ObjectId(current_user.id)}, {'$set': {'password': generate_password_hash(new_password)}})
                flash('Password updated successfully!', 'success')
                return redirect(url_for('profile'))
        else:
            # Allow user to update profile fields except username/email
            full_name = request.form.get('full_name', user_doc.get('full_name', ''))
            phone = request.form.get('phone', user_doc.get('phone', ''))
            city = request.form.get('city', user_doc.get('city', ''))
            users_collection.update_one({'_id': ObjectId(current_user.id)}, {'$set': {
                'full_name': full_name,
                'phone': phone,
                'city': city
            }})
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
    # Get events booked by user
    user_bookings = list(bookings_collection.find({'user_id': current_user.id}))
    booked_event_ids = [ObjectId(b['event_id']) for b in user_bookings]
    booked_events = list(events_collection.find({'_id': {'$in': booked_event_ids}})) if booked_event_ids else []
    # Get events hosted by user
    hosted_events = list(events_collection.find({'hosted_by': current_user.username}))
    return render_template('profile.html', user=user_doc, booked_events=booked_events, hosted_events=hosted_events, password_error=password_error)

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user_doc = users_collection.find_one({'email': email})
        if not user_doc:
            flash('No account found with that email.', 'danger')
            return render_template('forgot_password.html')
        otp = str(random.randint(100000, 999999))
        session['reset_email'] = email
        session['reset_otp'] = otp
        if send_otp_email(email, otp):
            flash('An OTP has been sent to your email. Please verify.', 'info')
            return redirect(url_for('reset_password'))
        else:
            flash('Failed to send OTP email. Please try again.', 'danger')
    return render_template('forgot_password.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if 'reset_email' not in session or 'reset_otp' not in session:
        flash('No password reset in progress.', 'danger')
        return redirect(url_for('forgot_password'))
    if request.method == 'POST':
        user_otp = request.form.get('otp')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        if user_otp != session['reset_otp']:
            flash('Invalid OTP. Please try again.', 'danger')
        elif new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
        elif len(new_password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
        else:
            users_collection.update_one({'email': session['reset_email']}, {'$set': {'password': generate_password_hash(new_password)}})
            session.pop('reset_email')
            session.pop('reset_otp')
            flash('Password reset successful! Please log in.', 'success')
            return redirect(url_for('login'))
    return render_template('reset_password.html')

if __name__ == "__main__":
    app.run(debug=True)
