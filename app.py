from flask import Flask, request, session, render_template, redirect, url_for, g
from json import dumps as tojson
from hashlib import sha1
from uuid import uuid4 as uuid
import itertools
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
def search():
  return render_template("search.html")

@app.route("/searched/")
def search_q(query):
  name_query = request.args.get('name_query', None)
  if name_query is not None:
    names = re.split(r'\W+', name_query)
    c = g.db.cursor()
    results = {}
    result_counts = {}
    for name in names:
      c.execute("SELECT num, dept, name FROM classes WHERE name LIKE '%%%s%%'", name)
      rows = c.fetchall()
      for result in rows:
        if result[0] in results:
          result_counts[result[0]] += 1
        else:
          results[result[0]] = result
          result_counts[result[0]] = 1
    sorted_results = sorted(result_counts.iteritems(), key=operator.itemgetter(1))
    sorted_results = [a for (a,b) in sorted_results]
    newresults = []
    for cnum in sorted_results:
      newresults += [results[cnum]]
    results = newresults
    return render_template("search_results.html", data=results)
  else:
    return render_template("search_results.html", data=[])

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

@app.route("/class/<int:num>/")
def get_class(num):
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
    return render_template("class.html", num=num, dept=dept, name=name,
                           units=units, desc=desc, pre=pre, co=co, lecs=lectures)
  else:
    c.close()
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


def gen_schedule(potential_classes,
                 wake_up_time=600,
                 end_time=2300,
                 min_units=36,
                 max_units=70):
  """
  Args:
      potential_classes: list of classes
        Each class should be an object containing fields:
            unit_count    (number)
            meeting_times
                dict of {lec num->(lecture days, start, end,
                          {rec_lett->(rec. day, start, end)})}
                e.g. {1: ('TR', 1500, 1640, {'A': ('MW', 1330, 1420)})}
            course_number (str)
            priority (float). infinite if mandatory
      wake_up_time: earliest class time
      end_time: latest class end time
      min_units, max_units: minimum and maximum number of units, respectively

   Returns list of lists of (course_num, lec_num, recitation). e.g.
   [[("15251", "1", "A"), ("15213", "2", "G"), ("80100", "1", "C")],
    [("15251", "1", "A"), ("15213", "2", "G"), ("76101", "1", "AA"), ("80180", "2", "D")]
    ]
  """
  def flatten_class(class_times):
    """Given a dict as in meeting_times (referenced above), return a flat list
    of possible lecture and recitation combinations.

    For example, given
      {1 : ("TR",300,600, {"A":("WF",1000,1100),
                           "B":("WF",1100, 1200),
                           "C":("WF",1330,1430)}),
       2 : ("TR",700,1000, {"D":("WF",1000,1100),
                            "E":("WF",1100,1200)})}
    return
      [("1", "A"), ("1", "B"), ("1", "C"), ("2", "D"), ("2", "E")]
    """
    class_list = []
    for lec_num, (_, _, _, rec_dict) in class_times.iteritems():
      for rec in rec_dict:
        class_list.append((lec_num, rec))
    return class_list

  # For each class, get the potential meetings
  # (this will be a map from course number to (class object,
  # possible times you can select for that class)
  possible_classes = {}
  for cls in potential_classes:
    possible_classes[cls.course_number] = (cls,
                                           flatten_class(cls.meeting_times))

  # First, filter out classes and recitations that are out of range.
  for cls, (obj, meetings) in possible_classes.iteritems():
    # m[0] will be the lecture number, m[1] will be the recitation letter.

    # Check lecture
    new_list = [m for m in meetings if (
      obj.meeting_times[m[0]][1] >= wake_up_time
      and obj.meeting_times[m[0]][2] <= end_time)]

    # Check recitation
    new_list = [m for m in new_list if (
      obj.meeting_times[m[0]][3][m[1]][1] >= wake_up_time
      and obj.meeting_times[m[0]][3][m[1]][2] <= end_time)]

    possible_classes[cls] = (obj, new_list)

  def powerset(iterable):
      "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
      s = list(iterable)
      return itertools.chain.from_iterable(
        itertools.combinations(s, r) for r in xrange(len(s)+1))

  # Then, try all subsets of classes (this will just have course numbers)
  class_combos = powerset(possible_classes)
  # Get rid of the ones with bad unit totals
  def unit_count(sched):
    return sum(cls.unit_count for cls in sched)
  class_combos = (sched for sched in class_combos if
                  min_units <= unit_count(sched) <= max_units)

  def all_times(cls):
    """Given a course number, get all possible meeting times as list."""
    obj = possible_classes[cls][0]
    lecture_based = [itertools.product(lec, obj.meeting_times[lec][3].keys())
        for lec in obj.meeting_times]
    return sum(lecture_based, [])

  # Add in recitations and lectures
  possible_schedules = (itertools.product(all_times(cls) for cls in sched)
                        for sched in class_combos)

  def get_bitmap_idx(time):
    """Get the bit idx to add time to"""
    idx = 0
    half_hour = time % 100
    assert half_hour == 30 or half_hour == 0
    if half_hour == 30:
      idx += 1
      time -= 30
    time /= 100
    idx += 2*time
    return idx

  def set_30_minutes(n, start, end):
    """Given 30-minute aligned start time, end time, and a bitmap to set,
    return False if there is a conflict or the value of n with start to end
    applied if not. """
    cur = start
    while cur < end:
      idx = get_idx(cur)
      if n & (1 << idx):
        return False
      else:
        n |= (1 << idx)
      if cur % 100 == 0:
        cur += 30
      else:
        assert cur % 100 == 30
        cur -= 30
        cur += 100
    return n

  # Filter out schedules with conflicts
  def has_conflict(sched):
    # Each day is a bitmap of 30 minute blocks (so, 48 bits). Bit 0 is
    # 00:00, bit 1 is 00:30, etc.
    days = {"M": 0, "T": 0, "W": 0, "R": 0, "F": 0}
    for cls, lec, rec in sched:
      obj = possible_classes[cls][0]
      lec_days, start, end, rec_dict = obj.meeting_times[lec]
      for day in lec_days:
        res = set_30_minutes(days[day], start, end)
        if res is False:
          return True  # Short-circuit
        days[day] = res
      rec_days, start, end = rec_dict[rec]
      for day in rec_days:
        res = set_30_minutes(days[day], start, end)
        if res is False:
          return True
        days[day] = res
    return False

  possible_schedules = (sched for sched in possible_schedules
                              if not has_conflict(sched))

  # Sort by getting tuples of (num_infinities, sum of non-infinite values).
  # Prioritize for num_infinities.
  sorted_sched = sorted(possible_schedules,
      key=(len(c for c, _, _ in possible_schedules
               if possible_classes[c][0].priority == float('inf')),
           sum(possible_classes[c][0].priority for c, _, _ in possible_schedules
               if possible_classes[c][0].priority != float('inf'))
          )
  return sorted_sched


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
