from flask import Flask, redirect, url_for, render_template, request, session, flash
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy import ForeignKey

app = Flask(__name__)
# sekret do sesji
app.secret_key = 'super_secret'
# okres czasu jaki informaje w sesji beda zapamietywane
app.permanent_session_lifetime = timedelta(minutes= 1)

app.config.update(
    DEBUG = True,
    ENV = 'develop',
    SQLALCHEMY_DATABASE_URI = "sqlite:///app.db",
    #SQLALCHEMY_DATABASE_URI = "mysql://root:toor123@127.0.0.1:3306/app",
    SQLALCHEMY_ECHO = True,
    SQLALCHEMY_TRACK_MODIFICATIONS = True
)

db = SQLAlchemy()
ma = Marshmallow()

db.app = app

db.init_app(app)
ma.init_app(app)

class users(db.Model):
    __tablename__ = 'users'
    _id = db.Column("id", db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    # tasks = db.relationship('tasks', backref='author', lazy='select')

    def __init__(self, name, email):
        self.name = name
        self.email = email


class tasks(db.Model):
    __tablename__ = 'tasks'
    _id = db.Column("id", db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    content = db.Column(db.String(200))
    user_id = db.Column(db.Integer, nullable=False)

    def __init__(self, title, content, user_id):
        self.title = title
        self.content = content
        self.user_id = user_id

@app.route('/index')
def home():
    return render_template("login.html")

@app.route('/login', methods=['POST', 'GET'])
def login():
    # jezeli wysylay jest formulaz metoda post obieramy dane zapisujemy w sesji
    if request.method == 'POST':
        session.permanent = True
        user = request.form["nm"]
        session["user"] = user

        found_user = users.query.filter_by(name = user).first()

        if found_user:
            session["email"] = found_user.email
        else:
            usr = users(user, "")
            db.session.add(usr)
            db.session.commit()

        flash("Zostaleś zalogowany!")
        return redirect(url_for("user"))
    else:
        # jezeli get wyswietlany jest formulaz lub jezeli zalogowany redirct do user
        if "user" in session:
            flash("jesteś już zalogowany!")
            return redirect(url_for("user"))
        else:
            flash("nie jesteś zalogowany")
            return render_template("login.html")

@app.route('/user', methods=['GET', 'POST'])
def user():
    email = None
    # jezeli mamy w sesji zapisany login wyswietlamy go
    if "user" in session:
        user = session["user"]

        if request.method == 'POST':
            email = request.form['email']
            session["email"] = email

            found_user = users.query.filter_by(name = user).first()
            found_user.email = email
            db.session.commit()

            flash("Email zostal zapisany")
        else:
            if "email" in session:
                email = session["email"]

        return render_template("user.html", email = email)
    else:
        # jezeli nie jest zalogowany redirect do formulaz
        return redirect(url_for("login"))

@app.route('/logout')
def logout():
    if "user" in session:
        user = session["user"]
        flash(f"Zostales wylogowany! {user}","info")
    session.pop("user", None)
    session.pop("email", None)
    return redirect(url_for("login"))

@app.route("/addTasks", methods=['GET', 'POST'])
def addTasks():
    if "user" in session:
        user = session["user"]

        if request.method == 'GET':
            return render_template("add_tasks.html")

        if request.method == 'POST':
            found_user = users.query.filter_by(name = user).first()
            task = tasks(
                title = request.form['title'],
                content = request.form['content'],
                user_id = found_user._id
            )
            db.session.add(task)
            db.session.commit()
            flash("zadanie zostało dodane!")
            return redirect(url_for("addTasks"))

    else:
        return redirect(url_for("user"))


@app.route('/tasks')
def viewTasks():
    if "user" in session:
        user = session["user"]
        foundUser = users.query.filter_by(name = user).first()
        userId = foundUser._id
        print(userId)
        userTasks = tasks.query.filter_by(user_id = userId)
        print(userTasks)
        return render_template("tasks.html", tasks = userTasks)

    else:
        flash("nie jesteś zalogowany")
        return redirect(url_for("login"))

@app.route('/<int:_id>', methods=['POST', 'GET'])
def delPost(_id):
    found_post = tasks.query.filter_by(_id = _id).delete()
    db.session.commit()
    db.session.remove()
    return redirect(url_for("viewTasks"))


# @app.route('/<name>')
# def user(name):
#     return f"Hello {name}!"

# @app.route('/admin')
# def admin():
#     return redirect(url_for("user", name="maslo"))

if __name__ == '__main__':
    db.create_all()
    app.run(host='0.0.0.0')
