from flask import Flask, request, redirect, url_for, flash, render_template, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
import random
import string
from email.message import EmailMessage
from flask_migrate import Migrate

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz_users.db'

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=True)  
    otp = db.Column(db.String(6), nullable=True)
    quizzes_taken = db.Column(db.Text, default='')

# Initialize Database
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Function to send OTP email
def send_otp_email(user, otp):
    msg = EmailMessage()
    msg['Subject'] = 'Your One-Time Password (OTP)'
    msg['From'] = 'your_email@example.com'
    msg['To'] = user.email
    msg.set_content(f'Your OTP code is: {otp}. Use this to log in.')
    
    with smtplib.SMTP('smtp.example.com', 587) as server:
        server.starttls()
        server.login('your_email@example.com', 'your_email_password')
        server.send_message(msg)

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long!', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists!', 'danger')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user is None:
            flash('Username does not exist!', 'danger')
            return redirect(url_for('login'))

        if not check_password_hash(user.password, password):
            flash('Incorrect password!', 'danger')
            return redirect(url_for('login'))

        login_user(user)
        flash('Login successful!', 'success')
        return redirect(url_for('profile'))

    return render_template('logiin.html')

# Route to request OTP
@app.route('/send_otp', methods=['GET', 'POST'])
def send_otp():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        
        if not user:
            
            temp_username = "user_" + ''.join(random.choices(string.ascii_letters + string.digits, k=6))
            user = User(username=temp_username, email=email, password=None)
            db.session.add(user)
            db.session.commit()

        
        otp = str(random.randint(100000, 999999))
        user.otp = otp
        db.session.commit()
        send_otp_email(user, otp)
        flash('OTP has been sent to your email!', 'success')
        session['email'] = email
        return redirect(url_for('login_with_otp'))

    return render_template('send_otp.html')

# Route to login with OTP
@app.route('/login_with_otp', methods=['GET', 'POST'])
def login_with_otp():
    if 'email' not in session:
        flash('Invalid access. Request OTP first.', 'danger')
        return redirect(url_for('send_otp'))

    if request.method == 'POST':
        entered_otp = request.form['otp']
        email = session['email']
        user = User.query.filter_by(email=email).first()

        if user and user.otp == entered_otp:
            user.otp = None
            db.session.commit()
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('profile'))
        else:
            flash('Invalid OTP!', 'danger')
            return redirect(url_for('login_with_otp'))

    return render_template('login_with_otp.html')

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        new_username = request.form['username']
        new_email = request.form['email']

        if new_username and new_email:
            current_user.username = new_username
            current_user.email = new_email
            db.session.commit()
            flash('Profile updated!', 'success')
        else:
            flash('Fields cannot be empty!', 'danger')

    return render_template('profile.html', user=current_user)

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    return render_template('forgot_password.html')

@app.route('/reset_password/<int:user_id>', methods=['GET', 'POST'])
def reset_password(user_id):
    return render_template('reset_password.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__': 
    app.run(debug=True)
