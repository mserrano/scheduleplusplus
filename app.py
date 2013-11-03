from flask import Flask, request, session, render_template, redirect, url_for, g
from json import dumps as tojson
from hashlib import sha1
from uuid import uuid4 as uuid
import MySQLdb
import re
import operator

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
def close_database_conn(_):
  db = getattr(g, 'db', None)
  if db is not None:
    db.close()

@app.route("/search/")
def search_page():
  return render_template("search.html")

def do_search(c, field, data, results, result_counts):
  array = re.split(r'\W+', data)
  for x in array:
    c.execute("SELECT num, dept, name FROM classes WHERE " + field + " LIKE %s", '%'+x+'%')
    rows = c.fetchall()
    for result in rows:
      if result[0] in results:
        result_counts[result[0]] += 1
      else:
        results[result[0]] = result
        result_counts[result[0]] = 1

@app.route("/searched/")
def search_q():
  name_query = request.args.get('name', None)
  desc_query = request.args.get('desc', None)
  results = {}
  result_counts = {}
  c = g.db.cursor()
  if name_query is not None and name_query is not '':
    do_search(c, "name", name_query, results, result_counts)
  if desc_query is not None and desc_query is not '':
    do_search(c, "description", desc_query, results, result_counts)
  sorted_results = sorted(result_counts.iteritems(), key=operator.itemgetter(1))
  sorted_results = [a for (a,b) in sorted_results]
  newresults = []
  for cnum in sorted_results:
    newresults += [results[cnum]]
  results = list(reversed(newresults))
  return render_template("search_results.html", data=results)

@app.route("/dept/<dept>/")
def get_classes_by_dept(dept):
  c = g.db.cursor()
  c.execute("SELECT num, name, units FROM classes WHERE dept=%s ORDER BY num ASC", dept)
  rows = c.fetchall()
  c.close()
  return render_template("dept.html", dept=dept, data=rows)

@app.route("/depts/")
def get_depts():
  c = g.db.cursor()
  c.execute("SELECT * FROM departments ORDER BY name ASC")
  rows = c.fetchall()
  c.close()
  return render_template("depts.html", data=rows)

def get_class_from_db(num):
  c = g.db.cursor()
  c.execute("SELECT * FROM classes WHERE num=%s LIMIT 1", str(num))
  rows = c.fetchall()
  if len(rows) > 0:
    num, dept, name, units, desc, pre, co = rows[0]
    c.execute("SELECT * FROM lectures WHERE cnum=%s", str(num))
    rows = c.fetchall()
    lectures = []
    for lec in rows:
      _, lnum, profs, days, time, room = lec
      c.execute("SELECT * FROM recitations WHERE cnum=%s AND lnum=%s", (str(num), lnum))
      newrows = c.fetchall()
      recitations = []
      for rec in newrows:
        recitations += [(rec[2], rec[3], rec[4], rec[5], rec[6])]
      lectures += [(lnum, profs, days, time, room, recitations, len(recitations) > 0)]
    c.close()
    return (num, dept, name, units, desc, pre, co, lectures)
  else:
    c.close()
    return None

@app.route("/class/<int:num>/")
def get_class(num):
  z = get_class_from_db(num)
  if z is not None:
    num, dept, name, units, desc, pre, co, lectures = z
    return render_template("class.html", num=num, dept=dept, name=name,
                           units=units, desc=desc, pre=pre, co=co, lecs=lectures)
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
  z = get_class_from_db(num)
  if z is not None:
    num, dept, name, units, desc, pre, co, lectures = z
    c = { 'num': num, 'dept': dept,'name': name,'units': units,'desc': desc,'pre': pre,'co': co }
    newlectures = {}
    for lecture in lectures:
      lnum, profs, days, time, room, recitations, _ = lecture
      o = { 'instructors': profs, 'days': days, 'time': time, 'room': room }
      newrecitations = {}
      for recitation in recitations:
        section, instructors, rdays, rtime, rroom = recitation
        newrecitations[section] = { 'instructors': instructors, 'days': rdays, 'time': rtime, 'room': rroom }
      o['recitations'] = newrecitations
      newlectures[lnum] = o
    c['lectures'] = newlectures
  else:
    c = {}  
  return tojson(c)

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


def gen_schedule(potential_classes,
                 wake_up_time=800,
                 consistent_lunchtime=False,
                 end_time=1700,
                 min_units=36,
                 max_units=70):
  """
  Args:
      potential_classes: dict of classes -> priority
        (infinite priority if mandatory).
        Each class should be an object containing fields:
            unit_count    (number)
            meeting_times
                dict of {lec num->(lecture days, start, end,
                          {rec_lett->(rec. day, start, end)})}
                e.g. {1: ('TR', 1500, 1640, {'A': ('MW', 1330, 1420)})}
            course_number (str)
      wake_up_time: earliest class time
      consistent_lunchtime: Should there be a consistent break in the middle of
        the day?
      end_time: latest class end time
      min_units, max_units: minimum and maximum number of units, respectively

   Returns list of lists of (course_num, lec_num, recitation). e.g.
   [[("15251", "1", "A"), ("15213", "2", "G"), ("80100", "1", "C")],
    [("15251", "1", "A"), ("15213", "2", "G"), ("76101", "1", "AA"), ("80180", "2", "D")]
    ]
  """
  pass


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
