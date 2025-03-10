from flask import Flask, request, redirect, url_for, flash, render_template, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string
from email.message import EmailMessage
import smtplib
from sqlalchemy import func, case
import requests

# Flask Configuration
app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ---- Database Models ----
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=True)
    otp = db.Column(db.String(6), nullable=True)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    question_text = db.Column(db.String(500), nullable=False, unique=True)
    answer = db.Column(db.String(200), nullable=False)
    option1 = db.Column(db.String(200), nullable=False)
    option2 = db.Column(db.String(200), nullable=False)
    option3 = db.Column(db.String(200), nullable=False)
    option4 = db.Column(db.String(200), nullable=False)

class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable=False)

class UserAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    user_answer = db.Column(db.String(200), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---- Authentication Routes ----
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/categories')
@login_required
def categories():
    return render_template('categories.html')

@app.route('/take_quiz/<difficulty>', methods=['GET'])
@login_required
def take_quiz(difficulty):
    # Map difficulty levels to API difficulty values
    difficulty_map = {
        "easy": "easy",
        "medium": "medium",
        "hard": "hard"
    }
    
    # Get the corresponding difficulty level for the API
    api_difficulty = difficulty_map.get(difficulty, "medium")
    
    # Fetch questions from OpenTDB API
    url = f'https://opentdb.com/api.php?amount=5&difficulty={api_difficulty}&type=multiple'
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        questions = []
        for item in data['results']:
            question = {
                "question_text": item['question'],
                "answer": item['correct_answer'],
                "options": item['incorrect_answers'] + [item['correct_answer']]
            }
            random.shuffle(question['options'])
            questions.append(question)
        
        # Render the quiz template with the questions
        return render_template('quiz.html', questions=questions, difficulty=difficulty)
    else:
        flash('Failed to fetch questions from the API.', 'danger')
        return redirect(url_for('categories'))

@app.route('/submit_quiz', methods=['POST'])
@login_required
def submit_quiz():
    score = 0
    total_questions = 0
    
    for question_text, user_answer in request.form.items():
        total_questions += 1
        question = Question.query.filter_by(question_text=question_text).first()
        if question and question.answer == user_answer:
            score += 1
    
    # Save the quiz result to the database
    quiz_result = QuizResult(
        user_id=current_user.id,
        category="General",  # You can change this based on your logic
        score=score
    )
    db.session.add(quiz_result)
    db.session.commit()
    
    flash(f'Quiz submitted! Your score: {score}/{total_questions}', 'success')
    return redirect(url_for('categories'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if len(password) < 8:
            flash('Password must be at least 8 characters!', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'danger')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful!', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('categories'))
        else:
            flash('Invalid username or password!', 'danger')
            return redirect(url_for('login'))
    
    return render_template('logiin.html')

@app.route('/profile', methods=['GET'])
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Successfully logged out', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)