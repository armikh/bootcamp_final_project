from flask import Flask, render_template, request, flash, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField
from wtforms.validators import DataRequired,Length
from flask_login import LoginManager

app = Flask(__name__)
app.secret_key = "6d82be61e7f69f492eecf153ec165754b3089ae4f7af02ac5699b42ff8b6680e"

@app.route('/')
def homepage():
    return render_template("homepage.html" , title = "Home")





class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=20)])
    submit = SubmitField('Login')





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

    return render_template('login.html', form=login_form, title = "login")


@app.route('/admin_dashboard')
def admin_dashboard():
    return render_template("admin_dashboard.html")


if __name__ == '__main__':
    app.run()