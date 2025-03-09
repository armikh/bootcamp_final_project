from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)


# Question Model
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    question_text = db.Column(db.String(500), nullable=False, unique=True)
    answer = db.Column(db.String(200), nullable=False)


# View All Questions
@app.route('/dashboard')
def dashboard():
    questions = Question.query.all()
    return render_template('dashboard.html', questions=questions)


# Add a Question
@app.route('/add_question', methods=['POST'])
def add_question():
    category = request.form['category']
    question_text = request.form['question_text']
    answer = request.form['answer']

    # Check if the question already exists
    existing_question = Question.query.filter_by(question_text=question_text).first()
    if existing_question:
        flash('This question already exists!', 'warning')
        return redirect(url_for('dashboard'))

    new_question = Question(category=category, question_text=question_text, answer=answer)
    db.session.add(new_question)
    db.session.commit()
    flash('Question added successfully!', 'success')
    return redirect(url_for('dashboard'))


# Delete a Question
@app.route('/delete_question/<int:id>')
def delete_question(id):
    question = Question.query.get_or_404(id)
    db.session.delete(question)
    db.session.commit()
    flash('Question deleted successfully!', 'danger')
    return redirect(url_for('dashboard'))


# Fetch Questions from External API
@app.route('/fetch_questions')
def fetch_questions():
    response = requests.get('https://opentdb.com/api.php?amount=5')
    data = response.json()

    new_questions = 0
    for item in data['results']:
        question_text = item['question'].strip()
        existing_question = Question.query.filter(Question.question_text == question_text).first()

        if not existing_question:
            question = Question(category=item['category'], question_text=question_text, answer=item['correct_answer'])
            db.session.add(question)
            new_questions += 1
    db.session.commit()

    if new_questions > 0:
        flash(f'{new_questions} new questions imported successfully!', 'success')
    else:
        flash('No new questions were added as all were duplicates.', 'warning')

    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        app.run(debug=True)
