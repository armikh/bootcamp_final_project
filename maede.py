from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, current_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import random
from datetime import datetime
import os

# Debug: Print the current working directory
print(f"Current working directory: {os.getcwd()}")

# Debug: Print a message to verify script execution
print("Starting the Flask application...")

# Create the Flask application instance
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for Flask-Login

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Debug: Print a message to verify database configuration
print("Configuring database...")

# Define the User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Define the Question model
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    question = db.Column(db.String(500), nullable=False)
    answer = db.Column(db.String(200), nullable=False)
    option1 = db.Column(db.String(200), nullable=False)
    option2 = db.Column(db.String(200), nullable=False)
    option3 = db.Column(db.String(200), nullable=False)
    option4 = db.Column(db.String(200), nullable=False)

# Define the QuizResult model
class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable=False)

# Debug: Print a message to verify model definitions
print("Defining models...")

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# Debug: Print a message to verify Flask-Login initialization
print("Initializing Flask-Login...")

# User loader function
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Home route
@app.route('/')
def home():
    return "Welcome to the Quiz App! <a href='/categories'>Take a Quiz</a>"

# Categories route
@app.route('/categories')
def categories():
    # Fetch unique categories from the database
    categories = db.session.query(Question.category).distinct().all()
    
    # Debug: Print the categories to the console
    print(f"Categories: {categories}")
    
    return render_template('categories.html', categories=categories)

# Quiz route
@app.route('/take_quiz/<category>', methods=['GET', 'POST'])
def take_quiz(category):
    if request.method == 'GET':
        # Fetch random questions from the database for the selected category
        questions = Question.query.filter_by(category=category).order_by(func.random()).limit(10).all()
        
        # Debug: Print the questions to the console
        print(f"Questions for category '{category}': {questions}")
        
        return render_template('quiz.html', questions=questions, category=category)
    
    elif request.method == 'POST':
        # Fetch the questions again for the selected category
        questions = Question.query.filter_by(category=category).order_by(func.random()).limit(10).all()
        
        # Calculate the user's score
        score = 0
        feedback = []
        for question in questions:
            user_answer = request.form.get(f'question_{question.id}')
            if user_answer == question.answer:
                score += 1
            else:
                feedback.append({
                    'question': question.question,
                    'correct_answer': question.answer,
                    'user_answer': user_answer
                })
        
        # Save the quiz result to the database
        quiz_result = QuizResult(user_id=1, category=category, score=score)  # Use a dummy user_id for testing
        db.session.add(quiz_result)
        db.session.commit()
        
        # Render the feedback page
        return render_template('feedback.html', score=score, total=len(questions), feedback=feedback)

# Debug: Print a message to verify route definitions
print("Defining routes...")

# Run the Flask application
if __name__ == '__main__':
    try:
        with app.app_context():
            print("Inside app context. Creating database tables...")
            db.drop_all()
            db.create_all()

            print("Adding sample questions...")
            sample_questions = [
                Question(
                    category='Python',
                    question='What is the output of print(2 ** 3)?',
                    answer='8',
                    option1='6',
                    option2='8',
                    option3='9',
                    option4='10'
                ),
                Question(
                    category='Python',
                    question='What is the output of print(3 * 4)?',
                    answer='12',
                    option1='7',
                    option2='12',
                    option3='15',
                    option4='20'
                ),
                Question(
                    category='SQL',
                    question='What does SQL stand for?',
                    answer='Structured Query Language',
                    option1='Structured Query Language',
                    option2='Simple Query Language',
                    option3='Standard Query Language',
                    option4='Sequential Query Language'
                ),
            ]
            db.session.add_all(sample_questions)
            db.session.commit()
    except Exception as e:
        print(f"Error during database setup: {e}")

    print("Starting Flask app...")
    app.run(debug=True)