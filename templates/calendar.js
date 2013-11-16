"use strict";

// Stolen from http://stackoverflow.com/q/55677
// Returns the position of the mouse click on the canvas.
function relMouseCoords(event){
    var totalOffsetX = 0;
    var totalOffsetY = 0;
    var canvasX = 0;
    var canvasY = 0;
    var currentElement = this;

    do{
        totalOffsetX += currentElement.offsetLeft - currentElement.scrollLeft;
        totalOffsetY += currentElement.offsetTop - currentElement.scrollTop;
    }
    while(currentElement = currentElement.offsetParent)

    canvasX = event.pageX - totalOffsetX - document.body.scrollLeft;
    canvasY = event.pageY - totalOffsetY - document.body.scrollTop;

    return {x:canvasX, y:canvasY}
}
HTMLCanvasElement.prototype.relMouseCoords = relMouseCoords;

var DEFAULT_START = 17, DEFAULT_END = 34;
function find_range(courses) {
    var min_start = null, max_end = null, sunday = false, saturday = false;
    for (var i = 0, j = courses.length; i < j; i++) {
        var course = courses[i];
        if (min_start === null || course.start < min_start) {
            min_start = course.start;
        }
        if (max_end === null || course.start + course.length > max_end) {
            max_end = course.start + course.length;
        }
        if (!sunday && course.days.search("U") >= 0) {
            sunday = true;
        }
        if (!saturday && course.days.search("S") >= 0) {
            saturday = true;
        }
    }
    return { start: Math.min(DEFAULT_START, min_start),
             end: Math.max(DEFAULT_END, max_end),
             days: (sunday ? "U" : "") + "MTWHF" + (saturday ? "S" : "") };
}

function time_to_string(d) {
    var on_30 = d % 2;
    var hour = Math.floor(d / 2);
    return (hour.toString() + (on_30 === 0 ? ":00" : ":30"));
}

function draw_grid(canvas, ctx, bounds) {
    var width = bounds.width, height = bounds.height;
    var num_vert = bounds.days.length + 1;
    var num_hori = bounds.end - bounds.start + 1;

    // First, draw vertical course lines and labels
    ctx.strokeStyle = "rgb(100,100,100)";
    ctx.beginPath();
    ctx.fillStyle = "rgb(50,50,50)";
    for (var i = 1; i < num_vert; i++) {
        ctx.moveTo(width * i, 0);
        ctx.lineTo(width * i, canvas.height);
        ctx.fillText(bounds.days.charAt(i - 1), width * i + 1, 1);
    }
    ctx.closePath();
    ctx.stroke();

    // Then, draw horizontal course lines and labels
    for (i = 1; i < num_hori; i++) {
        if ((i % 2) === 1) {
            ctx.strokeStyle = "rgb(100,100,100)";
        }
        else {
            ctx.strokeStyle = "rgb(200,200,200)";
        }
        ctx.beginPath();
        ctx.moveTo(0, height * i);
        ctx.lineTo(canvas.width, height * i);
        ctx.fillText(time_to_string(bounds.start + i), 1, height * i + 1);
        ctx.closePath();
        ctx.stroke();
    }
}

var CFL_SCALE = 10;
function draw_course(canvas, ctx, course, bounds,
                     cfl_idx, cfl_total, same_start)
// cfl_total: total number of conflicts occurred with course
// cfl_idx: conflict number for this course
// same_start: true if the conflicts start at the same time
{
    if (course.days.length !== 1) {
        console.log("Error! Course has not been split correctly");
    }
    var rect_idx = bounds.days.search(course.days);
    var cfl_frac = cfl_total / CFL_SCALE;
    if (!same_start) {
        var width = bounds.width - bounds.width * cfl_frac;
    }
    else {
        var width = bounds.width / (cfl_total + 1);
    }
    var height = course.length * bounds.height;
    if (!same_start) {
        var x = (rect_idx + 1) * bounds.width +
            (cfl_idx * bounds.width * cfl_frac);
    }
    else {
        var x = (rect_idx + 1) * bounds.width + (width * cfl_idx);
    }
    var y = (course.start - bounds.start + 1) * bounds.height;

    // Add text for each day as well
    ctx.fillRect(x, y, width, height);
    var rect_color = ctx.fillStyle;
    ctx.fillStyle = "rgb(0,0,0)";
    var text_width = ctx.measureText(course.course).width;

    // Line wrapping. Overflows with long single words :( fix that...
    // @TODO: Fix this
    if (text_width >= width - 1) {
        var words = course.course.split(/\-| /);
        for (var i = 0, j = words.length; i < j; i++) {
            ctx.fillText(words[i], x + 1, y + 1 +
                         (bounds.text_height * i));
        }
    }
    else {
        ctx.fillText(course.course, x + 1, y + 1);
    }
    ctx.fillStyle = rect_color;
    return {x: x, y: y, h: height, w: width};
}

function is_conflict(e1, e2) {
    if (e1.days !== e2.days) {
        return false;
    }
    if (e1.start >= e2.start && e1.start < (e2.start + e2.length)) {
        return true;
    }
    if (e1.start <= e2.start && (e1.start + e1.length) > e2.start) {
        return true;
    }
    return false;
}

function draw_courses(canvas, ctx, courses, bounds) {
    var course_locations = [];
    for (var i = 0, j = courses.length; i < j; i++) {
        var blue_color = Math.floor(((200 / j) * courses[i].id) + 50);
        var green_color = Math.floor(50 * (courses[i].id % 3) + 50);
        ctx.fillStyle = ("rgba(0, " + green_color.toString() + ", " +
                         blue_color.toString() + ", 0.8)");

        // Detect conflicts with other courses
        var cfl_idx = 0, cfl_total = 0, same_start = false;;
        for (var k = 0, h = courses.length; k < h; k++) {
            if (k !== i && is_conflict(courses[i], courses[k])) {
                if (k < i) {
                    cfl_idx++;
                }
                if (courses[i].start === courses[k].start) {
                    same_start = true;
                }
                cfl_total++;
            }
        }
        var loc = draw_course(canvas, ctx, courses[i], bounds,
                              cfl_idx, cfl_total, same_start);
        course_locations.push({course: courses[i], loc: loc});
    }
    return course_locations;
}

function courses_to_events(courses)
// Converts a list of courses that span multiple days to a list
// of events that occur at most once.
// For example, splits a MWF course into 3 events, one for each day.
{
    var events = [];
    for (var i = 0, j = courses.length; i < j; i++) {
        var course = courses[i];
        for (var k = 0; k < course.days.length; k++) {
            events.push({ course: course.course,
                          start: course.start,
                          length: course.length,
                          days: course.days.charAt(k),
                          id: i });
        }
    }
    return events;
}

function find_events(events, day, time) {
    var found = [];
    for (var i = 0, j = events.length; i < j; i++) {
        var event = events[i];
        if (day === event.days && time >= event.start &&
            time <= (event.start + event.length)) {
            found.push(event);
        }
    }
    return found;
}

function click_handler(canvas, course_locs, e)
// Event handler for mouse clicks on the canvas.
{
    var coords = canvas.relMouseCoords(e);
    var clicked_on = [];
    for (var i = 0, j = course_locs.length; i < j; i++) {
        var loc = course_locs[i].loc;
        if (coords.x >= loc.x && coords.x <= loc.x + loc.w &&
            coords.y >= loc.y && coords.y <= loc.y + loc.h) {
            clicked_on.push(course_locs[i].course);
        }
    }
    //@TODO: Something interactive and cool here.
    console.log("Clicked on course(s):", JSON.stringify(clicked_on));
}

function draw(courses)
// Takes a JSON object representing the course schedule and draws the
// calendar.
{
    // Uncomment for testing
    //courses = test_calendar_both_conflict;
    var canvas = document.getElementById("calendar");
    if (!canvas.getContext) {
        console.log("Canvas unsupported in browser!");
        return;
    }

    var ctx = canvas.getContext("2d");
    // Make sure to clear prior calendar
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (!courses) {
        console.log("Empty json? :(");
        return;
    }

    // Split out the JSON stuff
    courses = courses_to_events(courses);

    // Compute data needed to draw the scale and whatnot.
    var bounds = find_range(courses);
    bounds.width = canvas.width / (bounds.days.length + 1);
    bounds.height = canvas.height / (bounds.end - bounds.start + 1);
    bounds.text_height = Math.min(12, Math.floor(bounds.height) - 4);
    ctx.font = "bold " + bounds.text_height + "px sans-serif";
    ctx.textBaseline = "top";
    ctx.textAlign = "left";

    // First, draw the grid
    draw_grid(canvas, ctx, bounds);

    // Then, draw courses
    console.log("Drawing courses");
    var course_locs = draw_courses(canvas, ctx, courses, bounds);

    // Finally, install event handler
    canvas.addEventListener('click',
                            click_handler.bind(null, canvas, course_locs),
                            false);
}
