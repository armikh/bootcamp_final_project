from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField,IntegerField,RadioField,SelectField,TextAreaField
from wtforms.validators import DataRequired,Length, NumberRange
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
import requests


app = Flask(__name__)
app.secret_key = "6d82be61e7f69f492eecf153ec165754b3089ae4f7af02ac5699b42ff8b6680e"





#database related

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False)
    question_with_choices = db.Column(db.String(), nullable=False)
    answer = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f"Question {self.question_with_choices}"
    

with app.app_context():
    db.create_all()







#forms

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=20)])
    submit = SubmitField('Login')


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



#routes

@app.route('/')
def homepage():
    return render_template("homepage.html" , title = "Home")



@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()

    if request.method == "POST":
        if login_form.validate_on_submit():
            username = login_form.username.data
            password = login_form.password.data

            if username == "admin" and password == "admin123":
                flash('Login successful!', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Invalid username or password', 'error')

    return render_template('login.html', form=login_form, title = "Login")


@app.route('/admin_dashboard')
def admin_dashboard():
    return render_template("admin_dashboard.html", title = "Admin Dashboard")




@app.route('/admin_dashboard/add_question',methods=['GET','POST'])
def add_question():
    form = AddForm()
    if request.method == "POST":
        if form.validate_on_submit():
            full_question = (
                f"Question: {form.question_text.data}\n"
                f"Choices: {form.correct_answer.data},{form.incorrect_answer_1.data},{form.incorrect_answer_2.data},{form.incorrect_answer_3.data}"
            )
            new_question = Question(
                category=form.category.data,
                question_with_choices=full_question,
                answer=form.correct_answer.data
                )

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
            api_url = f"https://opentdb.com/api.php?amount={amount}&category={category}"
            response = requests.get(api_url)
            fetched_questions = response.json()

            #adding to database
            for q in fetched_questions["results"]:
                choices = q['incorrect_answers'] + [q['correct_answer']]
                question_with_choices = f"{q['question']}\nChoices: {', '.join(choices)}"
                new_question = Question(
                    category=q['category'],
                    question_with_choices=question_with_choices,
                    answer=q['correct_answer']
                )
                db.session.add(new_question)
            db.session.commit()
            return render_template("insert_successful.html",title="Insert Success",questions = fetched_questions['results'])
    return render_template("insert_qs.html",title="Insert Questions",form=insert_form)




if __name__ == '__main__':
    app.run()

