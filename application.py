import os
import requests

from flask import Flask, session, render_template, request, flash, redirect, url_for, abort
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from helpers import login_required

app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

goodreadsDevKey = "9k8LxnWmW5tXr6hd7iHQ"

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
databaseUrl="postgres://enhvtpzlqaqthl:19b766690ad0a2ff730ce39aa5cb0f7015ef453c8abd87e43510a9b5259beaab@ec2-54-228-212-134.eu-west-1.compute.amazonaws.com:5432/dbe1fo6q2mmjcf"
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route('/')
def index():
    return redirect(url_for('search'))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET" and session.get('u_id') is None:
        return render_template("login.html")
    elif request.method == "POST":
        uname = request.form.get("username")
        pin = request.form.get("password")
        row = db.execute("SELECT id,username,password FROM users WHERE username = :username ", {
                         "username": uname}).fetchone()
        if row is None:
            return "No entry found"
        elif pin != row.password or uname == "":
            return "Invalid Credentials"
        else:
            session["u_id"] = row.id
            return redirect(url_for('search'))
    else:
        return redirect(url_for('search'))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    elif request.method == "POST":
        u = request.form.get("username")
        p = request.form.get("password")
        p2 = request.form.get("password2")
        text = request.form.get("submit")
        if p != p2 or len(p) == len(p2) == 0 or len(u) == 0:
            return redirect(url_for('error'))
        else:
            db.execute("INSERT INTO users (username, password) VALUES (:username, :password)", {
                       "username": u, "password": p})
            db.commit()
            flash('Your account was created successfully!')
            return redirect("/")


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    if request.method == "GET":
        return render_template("search.html")
    elif request.method == "POST":
        keyword = request.form.get("keyword")
        keyword = "%"+keyword+"%"
        keyword = keyword.upper()
        radioOpt = request.form.get("inlineRadioOptions")
        if keyword.strip("%") == "":
            return "Empty KeyWord"
        if radioOpt == "option1":
            searchResults = db.execute(
                "SELECT * FROM books WHERE UPPER(title) LIKE :title ORDER BY year DESC", {"title": keyword}).fetchall()
        elif radioOpt == "option2":
            searchResults = db.execute(
                "SELECT * FROM books WHERE UPPER(author) LIKE :author ORDER BY year DESC", {"author": keyword}).fetchall()
        elif radioOpt == "option3":
            searchResults = db.execute("SELECT * FROM books WHERE year = :year ORDER BY author ASC", {
                                       "year":int(keyword.strip('%')) if keyword.strip('%').isnumeric() else 1 }).fetchall()
        elif radioOpt == "option4":
            searchResults = db.execute(
                "SELECT * FROM books WHERE isbn LIKE :isbn ORDER BY year DESC", {"isbn": keyword}).fetchall()
        return render_template("searchResult.html", searchResults=searchResults)


@app.route("/search_result/<isbn>", methods=["GET", "POST"])
@login_required
def bookDetails(isbn):
    if request.method == "GET":
        #create a connection
        print("get received")
        res = requests.get("https://www.goodreads.com/book/review_counts.json",
                           params={"key": goodreadsDevKey, "isbns": isbn})
        if res is None:
            return redirect(url_for('error'))
        json_data = res.json()["books"][0]
        book = db.execute(
            "SELECT * FROM books WHERE isbn = :isbn ORDER BY year DESC", {"isbn": isbn}).fetchone()
        revs = db.execute(
            "SELECT * FROM reviews WHERE isbn=:isbn", {"isbn": isbn}).fetchall()
        return render_template("book.html", book=book, json_data=json_data, revs=revs)
    elif request.method == "POST":
        print("post received")
        review = request.form.get("review")
        rating = request.form.get("inlineRadioOptions")
        user = db.execute("SELECT * FROM users WHERE id=:id",
                          {"id": session["u_id"]}).fetchone()
        review_count = db.execute("SELECT COUNT(*) FROM reviews WHERE reviewer = :reviewer AND isbn=:isbn", {
                                  "reviewer": user.username, "isbn": isbn}).fetchall()
        if len(review) != 0 and int(review_count[0][0]) == 0:
            book = db.execute(
                "SELECT * FROM books WHERE isbn = :isbn ORDER BY year DESC", {"isbn": isbn}).fetchone()
            db.execute("INSERT INTO reviews (isbn,reviewer,review,rating) VALUES (:isbn,:reviewer,:review,:rating)", {
                       "isbn": isbn, "reviewer": user.username, "review": review, "rating": rating})
            db.commit()
            return redirect(url_for("bookDetails", isbn=isbn))
        else:
            return "You have already posted"


@app.route('/logout')
@login_required
def logout():
    session.clear()
    return redirect(url_for('login'))



@app.route("/error")
def error():
    return abort(404)
