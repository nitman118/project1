import os
import requests

from flask import Flask, session, render_template,request,flash,redirect, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/", methods=["GET","POST"])
def login():
    if request.method=="GET":
        session.clear()
        return render_template("login.html")
    elif request.method=="POST":
        uname = request.form.get("username")
        pin=request.form.get("password")
        row=db.execute("SELECT id,username,password FROM users WHERE username = :username ",{"username":uname}).fetchone()
        if row is None:
            return "No entry found"
        elif pin!=row.password or uname=="":
            return "Invalid Credentials"
        else:
            session["u_id"]=row.id
            return render_template("search.html")


@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="GET":
        return render_template("register.html")
    elif request.method=="POST":
        u=request.form.get("username")
        p=request.form.get("password")
        p2=request.form.get("password2")
        text=request.form.get("submit")
        if p!=p2 or len(p)==len(p2)==0 or len(u)==0:
            return redirect(url_for('error'))
        else:
            db.execute("INSERT INTO users (username, password) VALUES (:username, :password)", {"username": u, "password": p})
            db.commit()
            flash('Your account was created successfully!')
            return redirect("/")

@app.route("/search", methods=["GET","POST"])
def search():
    if request.method=="GET":
        return render_template("search.html")

    elif request.method=="POST":
        radioOpt = request.form.get("inlineRadioOptions")
        return radioOpt



@app.route("/error")
def error():
    return "Error"
