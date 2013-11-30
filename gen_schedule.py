import itertools

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
          ))
  return sorted_sched

