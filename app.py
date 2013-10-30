from flask import Flask, request, session, render_template, redirect, url_for
from json import dumps as tojson
from hashlib import sha1
from uuid import uuid4 as uuid
import MySQLdb
import re

app = Flask('website')
app.config['DEBUG'] = True
app.secret_key = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'

def logged_in():
  return 'user' in session

def replace_classes(value):
  (newval, _) = re.subn(r'(\d{5})', r'<a href="/class/\1">\1</a>', value)
  return newval

app.jinja_env.filters['repclasses'] = replace_classes
app.jinja_env.globals['logged_in'] = logged_in

@app.before_request
def get_database_conn():
  g.db = MySQLdb.connect(host="localhost", user="spp",
                         passwd="XXXXXXXXXXXXXXXXXX", db="spp")

@app.teardown_request
def close_database_conn():
  db = getattr(g, 'db', None)
  if db is not None:
    db.close()

@app.route("/class/<int:num>/")
def get_class(num):
  c = g.db.cursor()
  c.execute("SELECT * FROM classes WHERE num=%s LIMIT 1", str(num))
  rows = c.fetchall()
  c.close()
  if len(rows) > 0:
    num, dept, name, units, desc, pre, co = rows[0]
    return render_template("class.html", num=num, dept=dept, name=name,
                           units=units, desc=desc, pre=pre, co=co)
  else:
    return render_template("class_failed.html", num=num)

@app.route("/api/search", methods=["POST"])
def search():
  """Return a list of classes matching the given terms
  (can be IDs, names, descriptions, professors...)"""
  pass


@app.route("/api/schedule", methods=["POST"])
def schedule():
  """Get a schedule satisfying the given constraints and possible classes."""
  pass


@app.route("/api/info/<course_num>")
def info(course_num):
  """Get info about the given course"""
  pass

@app.route("/login/", methods=["GET", "POST"])
def login():
  """Log the given user in"""
  if request.method == 'POST':
    username = request.form['username'].upper()
    if username == '':
      return render_template("login_failed.html", msg="Invalid username!")
    password = request.form['password']
    c = g.db.cursor()
    c.execute("SELECT id, sha_pass_hash FROM accounts WHERE username=%s LIMIT 1",
              username)
    rows = c.fetchall()
    c.close()
    if len(rows) == 0:
      return render_template("login_failed.html", msg="Unknown user!")
    i,p = rows[0]
    hsh = sha1(username + ':' + password).hexdigest().upper()
    if hsh == p:
      # yay successful login
      session['user'] = (i, username)
      return render_template("login_success.html")
    else:
      return render_template("login_failed.html", msg="Wrong password!")
  else:
    return render_template("login.html")

@app.route("/logout/")
def logout():
  """Log the given user out"""
  session.pop('user', None)
  return redirect(url_for('idx'))


@app.route("/register/", methods=["GET", "POST"])
def register():
  """Register a user"""
  if request.method == 'POST':
    # usernames are case-insensitive to avoid nonsense.
    username = request.form['username'].upper()
    if username == '':
      return render_template("reg_failed.html", msg="Invalid username!")
    password = request.form['password']
    # passwords are case-sensitive, because that's desirable.
    hsh = sha1(username + ':' + password).hexdigest().upper()
    success = False
    try:
      c = g.db.cursor()
      c.execute("INSERT INTO accounts (username, sha_pass_hash) VALUES (%s,%s)",
                (username, hsh))
      c.close()
      g.db.commit()
      success = True
    except:
      pass
    if success:
      return render_template("registered.html")
    else:
      return render_template("reg_failed.html",
                             msg="Username in use or database error!")
  else:
    return render_template("register.html")


@app.route("/api/save_schedule", methods=["GET", "POST"])
def save_schedule():
  """Save a created schedule to the database"""
  pass


@app.route("/api/get_user_schedules/<user>")
def get_user_schedules(user):
  """Get all schedules from a given user (subject to permissions)"""
  pass


@app.route("/api/get_schedule/<sched_id>")
def get_schedule(sched_id):
  """Get the given schedule id (subject to permissions)"""
  pass

@app.route("/")
def idx():
  return render_template("index.html")
