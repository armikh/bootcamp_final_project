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
from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField,IntegerField,SelectField
from wtforms.validators import DataRequired,Length, NumberRange
from html import unescape
from random import shuffle

# Flask Configuration
app = Flask(__name__)
app.secret_key = "6d82be61e7f69f492eecf153ec165754b3089ae4f7af02ac5699b42ff8b6680e"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///default.db'
app.config['SQLALCHEMY_BINDS'] = {
    'users': 'sqlite:///quiz_users.db',
    'quiz': 'sqlite:///quiz.db',
    'quiz_result': 'sqlite:///quiz_result.db',
    'user_answer': 'sqlite:///user_answer.db'

}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ---- Database Models ----
class User(UserMixin, db.Model):
    __bind_key__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=True)
    otp = db.Column(db.String(6), nullable=True)

class Question(db.Model):
    __bind_key__ = 'quiz'
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False)
    question_text = db.Column(db.String(500), nullable=False, unique=True)
    answer = db.Column(db.String(200), nullable=False)
    option1 = db.Column(db.String(200), nullable=False)
    option2 = db.Column(db.String(200), nullable=False)
    option3 = db.Column(db.String(200), nullable=False)
    option4 = db.Column(db.String(200), nullable=False)

    

class QuizResult(db.Model):
    __bind_key__ = 'quiz_result'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable=False)

class UserAnswer(db.Model):
    __bind_key__ = 'user_answer'
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, nullable=False)
    user_answer = db.Column(db.String(200), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)

with app.app_context():
    db.create_all()

# admin model
class Admin(UserMixin):
    def __init__(self, username, password):
        self.id = 156
        self.username = username
        self.password = password
        self.is_admin = True

admin_user = Admin(username="admin",password="admin123")


@login_manager.user_loader
def load_user(user_id):
    if int(user_id) == 156:
        return admin_user
    return User.query.get(int(user_id))

# ---- Authentication Routes ----
@app.route('/')
def index():
    return render_template('index.html')

# @app.route('/select_category')
# @login_required
# def select_category():
#     categories = db.session.query(Question.category).distinct().all()
#     category_names = [category[0] for category in categories]
#     return render_template("select_category.html", categories=category_names)

# @app.route('/take_quiz/<difficulty>', methods=['GET'])
# @login_required
# def take_quiz(difficulty):
#     # Map difficulty levels to API difficulty values
#     difficulty_map = {
#         "easy": "easy",
#         "medium": "medium",
#         "hard": "hard"
#     }
    
#     # Get the corresponding difficulty level for the API
#     api_difficulty = difficulty_map.get(difficulty, "medium")
    
#     # Fetch questions from OpenTDB API
#     url = f'https://opentdb.com/api.php?amount=5&difficulty={api_difficulty}&type=multiple'
#     response = requests.get(url)
    
#     if response.status_code == 200:
#         data = response.json()
#         questions = []
#         for item in data['results']:
#             question = {
#                 "question_text": item['question'],
#                 "answer": item['correct_answer'],
#                 "options": item['incorrect_answers'] + [item['correct_answer']]
#             }
#             random.shuffle(question['options'])
#             questions.append(question)
        
#         # Render the quiz template with the questions
#         return render_template('quiz.html', questions=questions, difficulty=difficulty)
#     else:
#         flash('Failed to fetch questions from the API.', 'danger')
#         return redirect(url_for('categories'))

# @app.route('/submit_quiz', methods=['POST'])
# @login_required
# def submit_quiz():
#     score = 0
#     total_questions = 0
    
#     for question_text, user_answer in request.form.items():
#         total_questions += 1
#         question = Question.query.filter_by(question_text=question_text).first()
#         if question and question.answer == user_answer:
#             score += 1
    
#     # Save the quiz result to the database
#     quiz_result = QuizResult(
#         user_id=current_user.id,
#         category="General",  # You can change this based on your logic
#         score=score
#     )
#     db.session.add(quiz_result)
#     db.session.commit()
    
#     flash(f'Quiz submitted! Your score: {score}/{total_questions}', 'success')
#     return redirect(url_for('categories'))
    


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
        if username == "admin" and password == "admin123":
            login_user(admin_user)
            return redirect(url_for('admin_dashboard'))
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('choose_category'))
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

#admin
#forms
class InsertForm(FlaskForm):
    amount = IntegerField("How Many Questions Would You Like To Insert?",validators=[DataRequired(),
                                                                                     NumberRange(min=1,message="The amount must be at least 1.")])
    category = SelectField("From Which Category?",choices=[],validators=[DataRequired()])
    submit = SubmitField('Insert')


class AddForm(FlaskForm):
    category = StringField('Category', validators=[DataRequired()])
    question_text = StringField('Question Text', validators=[DataRequired()])
    correct_answer = StringField('Correct Answer', validators=[DataRequired()])
    incorrect_answer_1 =StringField('Other Choices 1', validators=[DataRequired()])
    incorrect_answer_2 =StringField('Other Choices 1', validators=[DataRequired()])
    incorrect_answer_3 =StringField('Other Choices 1', validators=[DataRequired()])
    submit = SubmitField('Add Question')





@app.route('/admin_dashboard')
@login_required 
def admin_dashboard():
    return render_template("admin_dashboard.html", title = "Admin Dashboard")

@app.route('/homepage')
def homepage():
    categories = db.session.query(Question.category).distinct().all()
    category_names = [category[0] for category in categories]
    return render_template('homepage.html', categories=category_names)


def create_question(category, question_text, correct_answer, incorrect_answers):
    choices = incorrect_answers + [correct_answer]
    shuffle(choices)
    return Question(
        category=category,
        question_text=question_text,
        answer=correct_answer,
        option1=choices[0],
        option2=choices[1],
        option3=choices[2],
        option4=choices[3]
        )


@app.route('/admin_dashboard/add_question',methods=['GET','POST'])
def add_question():
    form = AddForm()
    if request.method == "POST":
        if form.validate_on_submit():
            new_question = create_question(
                category=form.category.data,
                question_text=unescape(form.question_text.data),
                correct_answer=unescape(form.correct_answer.data),
                incorrect_answers=[
                    unescape(form.incorrect_answer_1.data),
                    unescape(form.incorrect_answer_2.data),
                    unescape(form.incorrect_answer_3.data)])
            
            db.session.add(new_question)
            db.session.commit()
        return render_template("add_successful.html",title ="Add Successful" )
    return render_template("add_question.html",form=form,title ="Add Question")


@app.route('/admin_dashboard/view_questions')
def view_questions():
    all_questions = Question.query.all()
    return render_template("view_questions.html", questions=all_questions, title="View Question")

@app.route('/delete_question/<int:question_id>', methods=['POST'])
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    db.session.delete(question)
    db.session.commit()
    flash("Question deleted successfully!", "success")
    return redirect(url_for('view_questions'))


@app.route('/admin_dashboard/insert_question',methods=['GET','POST'])
def insert_question():
    api_url = "https://opentdb.com/api_category.php"
    response = requests.get(api_url)
    categories = []
    data = response.json()
    for category in data["trivia_categories"]:
        categories.append((str(category['id']), category['name']))

    insert_form = InsertForm()
    insert_form.category.choices = categories

    if request.method=="POST":
        if insert_form.validate_on_submit():
            amount = insert_form.amount.data
            category = insert_form.category.data
            api_url = f"https://opentdb.com/api.php?amount={amount}&category={category}&type=multiple"
            response = requests.get(api_url)
            fetched_questions = response.json()

            #adding to database
            for q in fetched_questions["results"]:
                new_question = create_question(
                    category=q['category'],
                    question_text=unescape(q['question']),
                    correct_answer=unescape(q['correct_answer']),
                    incorrect_answers=[unescape(ans) for ans in q['incorrect_answers']])
                db.session.add(new_question)

            db.session.commit()
            return render_template("insert_successful.html",title="Insert Success",questions = fetched_questions['results'])
    return render_template("insert_qs.html",title="Insert Questions",form=insert_form)



@app.route('/start_quiz', methods=['POST'])
def start_quiz():
    category = request.form.get('category')
    question_count = int(request.form.get('question_count'))

    available_questions = Question.query.filter_by(category=category).count()

    if available_questions >= question_count:
        questions = Question.query.filter_by(category=category).limit(question_count).all()
        return render_template("quiz.html", category=category, questions=questions)
    else:
        flash(f"Only {available_questions} questions are available in the '{category}' category.", "error")
        return redirect(url_for('choose_category'))
    

@app.route('/categories')
@login_required
def choose_category():
    categories = db.session.query(Question.category).distinct().all()
    category_names = [category[0] for category in categories]
    return render_template("choose_category.html", categories=category_names)


@app.route('/submit_quiz', methods=['POST'])
@login_required
def submit_quiz():
    score = 0
    results = []
    for question_id, selected_option in request.form.items():
        question = Question.query.get(int(question_id))
        if not question:
            flash("Invalid question ID.", "error")
            return redirect(url_for('choose_category'))

        is_correct = (selected_option == question.answer)
        if is_correct:
            score += 1

        user_answer = UserAnswer(
            question_id=question_id,
            user_answer=selected_option,
            is_correct=is_correct
        )
        db.session.add(user_answer)
        results.append({
                'question': question.question_text,
                'selected_option': selected_option,
                'correct_option': question.answer,
                'is_correct': is_correct})
    db.session.commit()

    total_questions = len(results)
    percentage_score = (score / total_questions) * 100 if total_questions > 0 else 0

    return render_template(
        "quiz_results.html",
        score=score,
        total_questions=total_questions,
        percentage_score=percentage_score,
        results=results)



# @app.route('/question_analysis')
# @login_required
# def question_analysis():
#     # Query all questions
#     questions = Question.query.all()

#     # Initialize a list to store analysis results
#     analysis_results = []

#     for question in questions:
#         # Count total answers for the question
#         total_answers = UserAnswer.query.filter_by(question_id=question.id).count()

#         # Count correct answers for the question
#         correct_answers = UserAnswer.query.filter_by(question_id=question.id, is_correct=True).count()

#         # Calculate correct answer rate
#         correct_answer_rate = (correct_answers / total_answers * 100) if total_answers > 0 else 0

#         # Append results for this question
#         analysis_results.append({
#             'question_id': question.id,
#             'question_text': question.question_text,
#             'total_answers': total_answers,
#             'correct_answers': correct_answers,
#             'correct_answer_rate': correct_answer_rate
#         })

#     return render_template("question_analysis.html", analysis_results=analysis_results)


@app.route('/question_analysis')
@login_required
def question_analysis():
    # Define a threshold for very low success rate (e.g., 30%)
    LOW_SUCCESS_RATE_THRESHOLD = 30

    # Query all questions
    questions = Question.query.all()

    # Initialize a list to store analysis results
    analysis_results = []

    for question in questions:
        # Count total answers for the question
        total_answers = UserAnswer.query.filter_by(question_id=question.id).count()

        # Count correct answers for the question
        correct_answers = UserAnswer.query.filter_by(question_id=question.id, is_correct=True).count()

        # Calculate correct answer rate
        correct_answer_rate = (correct_answers / total_answers * 100) if total_answers > 0 else 0

        # Append results for this question
        analysis_results.append({
            'question_id': question.id,
            'question_text': question.question_text,
            'total_answers': total_answers,
            'correct_answers': correct_answers,
            'correct_answer_rate': correct_answer_rate
        })

    # Identify questions with very low success rates (below the threshold)
    low_success_questions = [q for q in analysis_results if q["correct_answer_rate"] < LOW_SUCCESS_RATE_THRESHOLD]

    return render_template(
        "question_analysis.html", 
        analysis_results=analysis_results,  # All questions and their stats
        low_success_questions=low_success_questions,  # Questions with very low success rates
        low_success_threshold=LOW_SUCCESS_RATE_THRESHOLD  # Pass the threshold to the template
    )
    

if __name__ == '__main__':
    app.run()