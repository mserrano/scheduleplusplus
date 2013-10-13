import requests
from bs4 import *
import re

rnum = re.compile('[0-9]{5}')
def extract_course(link):
  if link.string is None:
    return None
  nm = link.string
  if rnum.match(nm):
    return str(int(nm))
  return None

def get_classes(dpt):
  url = "https://enr-apps.as.cmu.edu/open/SOC/SOCServlet?Formname=GET_CLASSES&"
  url = url + "SUBMIT=Retrieve+Schedule&SEMESTER=F13&GRAD_UNDER=All&MINI=NO&DEPT=" + dpt
  r = requests.get(url)
  b = BeautifulSoup(r.text)
  links = b.find_all('a')
  courses = [extract_course(link) for link in links]
  courses = [c for c in courses if c is not None]
  return courses

def get_details(c):
  url = "https://enr-apps.as.cmu.edu/open/SOC/SOCServlet?SEMESTER=F13&"
  url = url + "Formname=Course_Detail&CourseNo=" + c
  r = requests.get(url)
  txt = r.text.replace("</TR>", "</TR><TR>")
  b = BeautifulSoup(txt)
  bolds = b.find_all('b')
  title = bolds[1].string.replace(u'\xa0', '&')
  title = title[title.index('&&')+2:].strip()
  lecture = 0
  last = '0'
  sc = { 0: (None, {}) }
  table = b.table
  rows = table.findChildren('tr')[1:]
  units = None
  for row in rows:
    cells = row.findChildren('td')
    if units is None:
      for d in cells[2].descendants:
        x = d.string.strip()
        if len(x) > 0:
          units = int(float(x))
          break
    cells = [cell for cell in cells if cell.string is not None]
    if len(cells) < 8:
      continue
    if len(cells) > 0:
      sec = cells[2].string
      if not sec:
        sec = last
      last = sec.strip()
      sec = sec.strip()
      if 'Lec' in sec:
        # whee lecture
        lecture = int(sec[4:].strip())
        pr = str(cells[-1].string.strip().replace('\r\n', ';'))
        while ' ,' in pr:
          pr = pr.replace(' ,', ',')
        pr = pr.replace(';,', ';')
        rm = cells[-2].string.strip()
        while '  ' in rm:
          rm = rm.replace('  ', ' ')
        t1 = cells[-4].string.strip()
        t2 = cells[-3].string.strip()
        days = cells[-5].string.strip()
        if lecture not in sc:
          data = (pr, rm, days, t1 + "-" + t2)
          sc[lecture] = (data, {})
      elif 'Mini' in sec:
        sec = str(sec[5:].strip())
        pr = str(cells[-1].string.strip().replace('\r\n', ';'))
        while ' ,' in pr:
          pr = pr.replace(' ,', ',')
        pr = pr.replace(';,', ';')
        rm = cells[-2].string.strip()
        while '  ' in rm:
          rm = rm.replace('  ', ' ')
        t1 = cells[-4].string.strip()
        t2 = cells[-3].string.strip()
        days = cells[-5].string.strip()
        lecture = sec
        if lecture not in sc:
          data = (pr, rm, days, t1 + "-" + t2)
          sc[lecture] = (data, {})
      else:
        sec = sec.strip()
        pr = str(cells[-1].string.strip().replace('\r\n', ';'))
        while ' ,' in pr:
          pr = pr.replace(' ,', ',')
        pr = pr.replace(';,', ';')
        while pr[-1] == ',':
          pr = pr[:-1]
        rm = cells[-2].string.strip()
        while '  ' in rm:
          rm = rm.replace('  ', ' ')
        t1 = cells[-4].string.strip()
        t2 = cells[-3].string.strip()
        days = cells[-5].string.strip()
        data = (str(pr), str(rm), str(days), str(t1 + "-" + t2))
        sc[lecture][1][sec] = data
  txt2 = txt[txt.index('<BR><BR>')+8:]
  txt2 = txt2[txt2.index('<BR><BR>'):]
  b = BeautifulSoup(txt2)
  fonts = b.find_all('font')
  description = fonts[1].string.strip() if fonts[1].string else "No description."
  description = description.replace('\r', '')
  prereqs = fonts[3].string.strip()
  coreqs = fonts[5].string.strip().replace('\r\n','')
  while ' ,' in coreqs or '  ' in coreqs:
    coreqs = coreqs.replace(' ,', ',')
    coreqs = coreqs.replace('  ', ' ')
  return title, units, description, prereqs, coreqs, sc

def fmt(num, (title, units, desc, pre, co, sc)):
  print num, title, "(%s units)" % str(units)
  if len(desc) > 0:
    print desc
  else:
    print "No description."
  print "Prerequisites:", pre
  print "Corequisites:", co
  for lecture in sc:
    if lecture != 0:
      data = sc[lecture][0]
      professors = data[0]
      room = data[1]
      days = data[2]
      time = data[3]
      print "Lecture %s\n\t%s\n\t%s\n\t%s\n\t%s" % (str(lecture), professors, room, days, time)
    for recitation in sc[lecture][1]:
      data = sc[lecture][1][recitation]
      TA = data[0]
      room = data[1]
      day = data[2]
      time = data[3]
      print "\tSection %s\n\t\t%s\n\t\t%s\n\t\t%s\n\t\t%s" % (recitation, TA, room, day, time)
  return None

# grab all the math classes for testing purposes
cl = get_classes("MSC")
for c in cl:
  fmt(c, get_details(c))
