import requests
from json import loads as parse
from bs4 import *
import re

appID = 'XXXXXXXXXXXXXXXXXXXXXX'
secretKey = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXx'
semester = 'S14'
baseurl = 'https://apis.scottylabs.org/v1/schedule/'

rnum = re.compile('[0-9]{5}')
def extract_course(link):
  if link.string is None:
    return None
  nm = link.string
  if rnum.match(nm):
    return nm
  return None

def get_classes(dpt):
  url = "https://enr-apps.as.cmu.edu/open/SOC/SOCServlet?Formname=GET_CLASSES&"
  url = url + "SUBMIT=Retrieve+Schedule&SEMESTER=" + semester + "&GRAD_UNDER=All&MINI=NO&DEPT="+ dpt
  r = requests.get(url)
  b = BeautifulSoup(r.text)
  links = b.find_all('a')
  courses = [extract_course(link) for link in links]
  courses = [c for c in courses if c is not None]
  return courses

def get_details(c):
  try:
    url = "https://enr-apps.as.cmu.edu/open/SOC/SOCServlet?SEMESTER=" + semester + "&"
    url = url + "Formname=Course_Detail&CourseNo=" + c
    r = requests.get(url)
    txt = r.text.replace("</TR>", "</TR><TR>")
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
  except:
    coreqs = prereqs = description = "Could not obtain data."
  url = build_url('courses/' + c)
  try:
    j = requests.get(url).text
    j = parse(j)
    j = j['course']
    title = j['name']
    units = str(j['units'])
    lectures = j['lectures']
  except:
    lectures = title = units = "Not found."
  return c, title, units, description, prereqs, coreqs, lectures

def lec_to_str(lecture):
  if 'name' in lecture:
    return lecture['name'] + " " + ("(" + lecture['section'] + ", " + lecture['instructors'] +
      ", " + lecture['days'] + ", " + lecture['location'] + ", " + lecture['time_start'] + "-" +
      lecture['time_end'] + ")")
  else:
    return lecture['section'] + " " + ("(" + lecture['instructors'] + ", " + lecture['days'] + ", "
      + lecture['location'] + ", " + lecture['time_start'] + "-" + lecture['time_end'] + ")")

def removeNonAscii(s): return "".join(i for i in s if ord(i)<128)

def fmt((num, title, units, description, prereqs, coreqs, lectures)):
  print num, "-", title, "(" + units + " units)"
  print "\tDescription:",  removeNonAscii(description)
  print "\tPrereqs:", prereqs
  print "\tCoreqs:", coreqs
  for lecture in lectures:
    print "\t" + lec_to_str(lecture)
    if 'recitations' in lecture:
      for recitation in lecture['recitations']:
        print "\t\t" + lec_to_str(recitation)

def build_url(target):
  return baseurl + semester + '/' + target + '?app_id=' + appID + '&app_secret_key=' + secretKey

def flatten(l):
  return (x for y in l for x in y)

depts = ['AFR', 'ARC', 'ART', 'BXA', 'BSC', 'BMD', 'BA', 'CFA', 'CIT', 'CMU', 'CAS', 'CNB',
         'CHE', 'CMY', 'CEE', 'CB', 'CS', 'BCA', 'CRM', 'DES', 'HSS', 'DRA', 'ECO', 'ECE',
         'IAE', 'EPP', 'ENG', 'ETC', 'H00', 'ISH', 'HC', 'HIS', 'HCI', 'BHA', 'ICT', 'INI',
         'ISM', 'ISR', 'LTI', 'MCS', 'MLG', 'MSE', 'MSC', 'MEG', 'MED', 'MST', 'ML', 'MUS',
         'NVS', 'PHI', 'PE', 'PHY', 'PSY', 'PMP', 'PPP', 'ROB', 'BSA', 'SV', 'SDS', 'SE',
         'STA', 'STU', 'IA']

classes = flatten(get_classes(d) for d in depts)
class_details = (get_details(c) for c in classes)
for d in class_details:
  fmt(d)
