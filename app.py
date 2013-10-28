from flask import Flask, request, session, render_template
from json import dumps as tojson
from hashlib import sha1
import MySQLdb

app = Flask('website')
app.config['DEBUG'] = True

@app.route("/class/<int:num>/")
def c(num):
  db = MySQLdb.connect(host="localhost", user="spp",
                       passwd="XXXXXXXXXXXXXXXXXX", db="spp")
  c = db.cursor()
  x = c.execute("SELECT * FROM classes WHERE num=%s", str(num))
  rows = c.fetchall()
  for r in rows:
    num, dept, name, units, desc, pre, co = r
  c.close() 
  db.close()
  return render_template("class.html", num=num, dept=dept, name=name,
                         units=units, desc=desc, pre=pre, co=co)

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


@app.route("/login", methods=["GET", "POST"])
def login():
  """Log the given user in"""
  pass


@app.route("/logout")
def logout():
  """Log the given user out"""
  pass


@app.route("/register/", methods=["GET", "POST"])
def register():
  """Register a user"""
  if request.method == 'POST':
    username = request.form['username'].upper()
    if username == '':
      return render_template("reg_failed.html", msg="Invalid username!")
    password = request.form['password']
    db = MySQLdb.connect(host='localhost', user='spp',
                         passwd='XXXXXXXXXXXXXXXXXX', db='spp')
    c = db.cursor()
    # yes, this means our passwords are case-insensitive. I don't
    # really care
    hsh = sha1(username + ':' + password.upper()).hexdigest().upper()
    success = False
    try:
      c = db.cursor()
      c.execute("INSERT INTO accounts (username, sha_pass_hash) VALUES (%s,%s)",
                (username, hsh))
      c.close()
      db.commit()
      success = True
    except:
      pass
#    db.commit()
    db.close()
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
