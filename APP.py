from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = "courtship_system_secret_key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///courtship.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models (Tables)
class Man(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), default='Male')
    location = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    selected_partner_id = db.Column(db.Integer, nullable=True)

class Woman(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), default='Female')
    location = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    selected_partner_id = db.Column(db.Integer, nullable=True)

class Pairing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    man_id = db.Column(db.Integer, db.ForeignKey('man.id'))
    woman_id = db.Column(db.Integer, db.ForeignKey('woman.id'))
    status = db.Column(db.String(20), default='Paired')

with app.app_context():
    db.create_all()

# Helper function to send email
def send_email(to_email, subject, body):
    sender_email = "maselesimon113@gmail.com"
    sender_password = "your_app_password"  # Weka App Password yako hapa
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = to_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())
    except Exception as e:
        print("Email sending failed:", e)

# Routes
@app.route('/')
def home():
    admin_info = {
        "email": "subalosimon26@gmail.com",
        "phone": "0634359132",
        "location": "Shinyanga, Tanzania"
    }
    return render_template('index.html', admin=admin_info)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        phone = request.form['phone']
        age = request.form['age']
        gender = request.form['gender']
        location = request.form['location']
        password = generate_password_hash(request.form['password'])

        # Kuzuia error ya kuingiza email inayofanana
        existing_man = Man.query.filter_by(email=email).first()
        existing_woman = Woman.query.filter_by(email=email).first()

        if existing_man or existing_woman:
            flash('Email hii tayari imeshasajiliwa! Tafadhali tumia email nyingine au ingia (Login).', 'danger')
            return redirect(url_for('register'))

        if gender == 'Male':
            user = Man(full_name=full_name, email=email, phone_number=phone, age=age, location=location, password=password)
        else:
            user = Woman(full_name=full_name, email=email, phone_number=phone, age=age, location=location, password=password)

        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        man = Man.query.filter_by(email=email).first()
        woman = Woman.query.filter_by(email=email).first()

        user = man or woman
        gender = 'Male' if man else 'Female' if woman else None

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['gender'] = gender
            session['name'] = user.full_name
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    gender = session['gender']

    if request.method == 'POST':
        selected_id = request.form['selected_partner_id']
        if gender == 'Male':
            man = Man.query.get(user_id)
            man.selected_partner_id = selected_id
        else:
            woman = Woman.query.get(user_id)
            woman.selected_partner_id = selected_id
        db.session.commit()
        flash('Selection sent to admin successfully!', 'info')

    men_count = Man.query.count()
    women_count = Woman.query.count()

    opposite_gender_list = Woman.query.all() if gender == 'Male' else Man.query.all()

    return render_template('dashboard.html', men_count=men_count, women_count=women_count, partners=opposite_gender_list)

# Route ya Login ya Admin
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Hapa unaweza kubadilisha username na password unazotaka kutumia
        if username == "admin" and password == "admin123":
            session['is_admin'] = True
            flash('Welcome Admin!', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Username au Password ya Admin siyo sahihi!', 'danger')

    return render_template('admin_login.html')

# Route ya Admin Dashboard (Iliyolindwa)
@app.route('/admin')
def admin():
    if not session.get('is_admin'):
        flash('Huna ruhusa ya kuingia hapa! Ingia kama Admin kwanza.', 'danger')
        return redirect(url_for('admin_login'))

    men = Man.query.all()
    women = Woman.query.all()
    men_count = len(men)
    women_count = len(women)
    pairings = Pairing.query.all()

    return render_template('admin.html', men=men, women=women, men_count=men_count, women_count=women_count, pairings=pairings)

@app.route('/admin/pair', methods=['POST'])
def pair_users():
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))

    man_id = request.form.get('man_id')
    woman_id = request.form.get('woman_id')

    if man_id and woman_id:
        pairing = Pairing(man_id=man_id, woman_id=woman_id)
        db.session.add(pairing)
        db.session.commit()

        man = Man.query.get(man_id)
        woman = Woman.query.get(woman_id)

        # Utumaji wa taarifa
        subject = "Courtship System - You Have Been Paired!"
        body_man = f"Hello {man.full_name},\n\nYou have been paired with {woman.full_name}. Contact: {woman.email}, Phone: {woman.phone_number}."
        body_woman = f"Hello {woman.full_name},\n\nYou have been paired with {man.full_name}. Contact: {man.email}, Phone: {man.phone_number}."

        send_email(man.email, subject, body_man)
        send_email(woman.email, subject, body_woman)

        flash(f'Successfully paired {man.full_name} and {woman.full_name}!', 'success')
    else:
        flash('Pairing failed. Please select valid users.', 'danger')

    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
