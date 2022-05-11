from hashlib import sha256
from flask import Flask, session
from flask import render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from flask_bootstrap import Bootstrap

from werkzeug.security import generate_password_hash, check_password_hash
import os

from datetime import datetime, timedelta
import pytz


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reserve.db'
app.config['SECRET_KEY'] = os.urandom(24)

db = SQLAlchemy(app)
bootstrap = Bootstrap(app)

login_Manager = LoginManager()
login_Manager.init_app(app)

@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=30)
    session.modified = True

class Reservation(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  location = db.Column(db.String(20), nullable=False)
  purpose =  db.Column(db.String(50), nullable=False)
  start_time = db.Column(db.String(30), nullable=False)
  end_time = db.Column(db.String(30), nullable=False)
  created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(pytz.timezone("Asia/Tokyo")))
  auther_id = db.Column(db.Integer(), nullable=False)
  auther_name = db.Column(db.String(), nullable=False)

class User(UserMixin, db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username =  db.Column(db.String(20), unique=True)
  password = db.Column(db.String(20))

@login_Manager.user_loader
def load_user(user_id):
  return User.query.get(user_id)

@app.route("/", methods=["GET","POST"])
@login_required
def index():
  if request.method == "GET":
    reservations = Reservation.query.all()
  return render_template("index.html", reservations=reservations)

@app.route("/signup", methods=["GET", "POST"])
def signup():
  if request.method == "POST":
    username = request.form.get("username")
    password = request.form.get("password")
    c_password = request.form.get("c-password")

    if password == c_password:
      user = User(username=username, password=generate_password_hash(password, method='sha256'))
      
      db.session.add(user)
      db.session.commit()

      return redirect("/login")

    else:
      return redirect("/error")

  else:
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
  if request.method == "POST":
    username = request.form.get("username")
    password = request.form.get("password")

    user = User.query.filter_by(username=username).first()
    if check_password_hash(user.password, password):
      login_user(user)
      return redirect("/")

  else:
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

@app.route("/reserve", methods=["GET", "POST"])
@login_required
def reserve():
  if request.method == "POST":
    location = request.form.get("location")
    purpose = request.form.get("purpose")
    start_time=request.form.get("start-time")
    end_time=request.form.get("end-time")
    auther_id = current_user.id
    auther_name = current_user.username

    reservation = Reservation(location=location, purpose=purpose,start_time=start_time, end_time=end_time, auther_id=auther_id, auther_name=auther_name)
    
    db.session.add(reservation)
    db.session.commit()
    return redirect("/complete")

  else:
    return render_template("reserve.html")

@app.route("/complete")
@login_required
def complete():
  return render_template("complete.html")
  
@app.route("/error")
def error():
  return render_template("error.html")

@app.route("/<int:id>/update", methods=["GET", "POST"])
@login_required
def update(id):
  reservation = Reservation.query.get(id)
  
  if current_user.id == reservation.auther_id:

    if request.method == "GET":
      return render_template("update.html",reservation=reservation)
    else:
      reservation.purpose = request.form.get("purpose")
      reservation.start_time = request.form.get("start-time")
      reservation.end_time = request.form.get("end-time")

      db.session.commit()
      return redirect("/complete")

  else:
    return redirect("/")

@app.route("/<int:id>/userupdate", methods=["GET", "POST"])
@login_required
def userupdate(id):
  user = User.query.get(id)

  if request.method == "GET":
    return render_template("user_update.html",user=user)
  else:
    user.username = request.form.get("username")

    db.session.commit()
    return redirect("/complete")

@app.route("/<int:id>/delete", methods=["GET"])
@login_required
def delete(id):
  reservation = Reservation.query.get(id)
  if current_user.id == reservation.auther_id:
    db.session.delete(reservation)
    db.session.commit()
    return redirect("/")
  else:
    return redirect("/")