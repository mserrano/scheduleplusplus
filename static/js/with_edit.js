function isEmpty(o) {
  for (var i in o) { if (o.hasOwnProperty(i)) return false; }
  return true;
}
function launchModal(cnum) {
  $.get("/api/info/".concat(cnum,"/"),
        function(data, status) {
          if (isEmpty(data)) {
            BootstrapDialog.alert("Class not found!");
            return;
          }
          var desc = data.desc;
          var dept = data.dept;
          var coreqs = data.co;
          var prereqs = data.pre;
          var units = data.units;
          var lectures = data.lectures;
          var name = data.name;
          var str = '<a href="/class/'.concat(cnum,'/">');
          str = str.concat(data.name, '</a>');
          BootstrapDialog.show({
            closable: false,
            message:
              function(dialogRef) {
                var $message = $('<div><p><a href="/class/' + cnum + '/">' + name + '</a></p><p>' + desc + '</p></div>');
                for (var lnum in lectures) {
                  var lecture = lectures[lnum];
                  if (isEmpty(lecture.recitations)) {
                    var $s = $("<div>".concat(lnum, " ", lecture.instructors, " ", lecture.days, "</div>"));
                    var $button = $('<button class="btn btn-sm">Add to Schedule</button>');
                    $button.on('click', {dialogRef: dialogRef, cnum: cnum, lnum: lnum},
                              function(event) {
                                addCourse(event.data.cnum, event.data.lnum, 'None');
                                dialogRef.close();
                              });
                    $button.appendTo($s);
                    $message.append($s);
                  }
                  else {
                    var $s1 = $("<div>".concat(lnum, " ", lecture.instructors, " ", lecture.days, "</div>"));
                    for (var section in lecture.recitations) {
                      var rec = lecture.recitations[section];
                      var $s2 = $("<div>".concat(section, " ", rec.instructors, " ", rec.days, "</div>"));
                      var $button = $('<button class="btn btn-sm">Add to Schedule</button>');
                      $button.on('click', {dialogRef: dialogRef, cnum: cnum, lnum: lnum, section: section},
                                  function(event) {
                                    addCourse(event.data.cnum, event.data.lnum, event.data.section);
                                    dialogRef.close();
                                  });
                      $button.appendTo($s2);
                      $s2.appendTo($s1);
                    }
                    $message.append($s1);
                  }
                }
                return $message;
              },
            buttons: [{
               label: 'Close',
               action: function(dialogRef) {
                 dialogRef.close();
              }
            }]
          });
        });
}

function refreshSched(a, b) {
  $.get("/api/get_schedule/" + sched_num + "/",
        function(data, status) {
          draw(data.schedule);

          // do some course-list updating.
          var str = '<p>Add a course:<br /><form name="course_add" action="" method="GET" onsubmit="doSearch(this); return false;">Course number: <input type="text" name="cnum" value="" /><br /><input type="button" name="button" value="Add Course" onclick="doSearch(this.form);" /></form></p>';
          for (var i = 0; i < data.courses.length; i++) {
            var course = data.courses[i];
            var cstr = '<p><a href="/class/';
            cstr = cstr.concat(course.num);
            cstr = cstr.concat('">',course.num,' ',course.name,'</a> <a href="#" onclick="removeCourse(', course.num, ')">(Remove)</a></p>');
            str = str.concat(cstr);
          }
          $('#courseList').html(str);
        });
}

function addCourse(cnum, lnum, section) {
  $.post("/api/add_to_schedule/",
        { "num": sched_num, "cnum": cnum, "lnum": lnum, "section": section },
        refreshSched);
}
function doSearch(form) {
  var val = "" + form.cnum.value;
  if (val.indexOf("-") != -1) {
    val = val.replace("-", "");
  }
  launchModal(val);
}
function removeCourse(cnum) {
  $.post("/api/remove_from_schedule/",
         { "num": sched_num, "cnum": cnum },
         refreshSched);
}

