from flask import Flask, request

@app.route("/search", methods=["POST"])
def search():
  """Return a list of classes matching the given terms
  (can be IDs, names, descriptions, professors...)"""
  pass


@app.route("/schedule", methods=["POST"])
def schedule():
  """Get a schedule satisfying the given constraints and possible classes."""
  pass


@app.route("/info/<course_num>")
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


@app.route("/register", methods=["GET", "POST"])
def register():
  """Register a user"""
  pass


@app.route("/save_schedule", methods=["GET", "POST"])
def save_schedule():
  """Save a created schedule to the database"""
  pass


@app.route("/get_user_schedules/<user>")
def get_user_schedules(user):
  """Get all schedules from a given user (subject to permissions)"""
  pass


@app.route("/get_schedule/<sched_id>")
def get_schedule(sched_id):
  """Get the given schedule id (subject to permissions)"""
  pass
