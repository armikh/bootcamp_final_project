from flask import Flask, render_template, request
from flask_wtf import FlaskForm
from wtforms import RadioField, SubmitField

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'

class MultipleChoiceForm(FlaskForm):
    question = "What is the capital of France?"
    choices = [('paris', 'Paris'), ('london', 'London'), ('berlin', 'Berlin'), ('madrid', 'Madrid')]
    answer = RadioField(question, choices=choices)
    submit = SubmitField('Submit')

@app.route('/', methods=['GET', 'POST'])
def index():
    form = MultipleChoiceForm()
    if request.method == "POST":    
        if form.validate_on_submit():
            selected_answer = form.answer.data
            return f"Selected Answer: {selected_answer}"
    return render_template('add_test.html', form=form)

if __name__ == '__main__':
    app.run(port ="8000")
