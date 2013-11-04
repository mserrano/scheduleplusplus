"use strict";

var test_calendar_normal = [
    { course: "18-213 M",
      start: 33,
      length: 2,
      days: "M" },
    { course: "15-322 A",
      start: 21,
      length: 3,
      days: "TH" },
    { course: "15-210 1",
      start: 24,
      length: 3,
      days: "TH" },
    { course: "79-345 A",
      start: 27,
      length: 3,
      days: "TH" },
    { course: "18-213 2",
      start: 37,
      length: 2,
      days: "TH" },
    { course: "15-210 A",
      start: 21,
      length: 2,
      days: "W" },
    { course: "79-345 A",
      start: 37,
      length: 6,
      days: "W" }
];

var test_calendar_sunday = [
    { course: "79-345 A",
      start: 37,
      length: 6,
      days: "W" },
    { course: "Day Drinking",
      start: 20,
      length: 10,
      days: "U" }
];

var test_calendar_saturday = [
    { course: "Parties",
      start: 9,
      length: 30,
      days: "S" },
    { course: ":(",
      start: 20,
      length: 20,
      days: "MTWHF" }
];

var test_calendar_weekend = [
    { course: "Parties",
      start: 5,
      length: 30,
      days: "S" },
    { course: ":(",
      start: 20,
      length: 20,
      days: "MTWHF" },
    { course: "Day Drinking",
      start: 20,
      length: 10,
      days: "U" }
];

var test_calendar_start_conflict = [
    { course: "Something",
      start: 20,
      length: 3,
      days: "F" },
    { course: "Naptime",
      start: 20,
      length: 10,
      days: "MWF" }
];

var test_calendar_mid_conflict = [
    { course: "Something Else",
      start: 18,
      length: 4,
      days: "F" },
    { course: "Naptime",
      start: 20,
      length: 10,
      days: "MWF" }
];

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
    return { start: min_start, end: max_end,
             days: (sunday ? "U" : "") + "MTWHF" + (saturday ? "S" : "") };
}

function date_to_string(d) {
    var on_30 = d % 2;
    var hour = Math.floor(d / 2);
    return (hour.toString() + (on_30 === 0 ? ":00" : ":30"));
}

function draw_grid(canvas, ctx, bounds) {
    var width = bounds.width, height = bounds.height;
    var num_vert = bounds.days.length + 1;
    var num_hori = bounds.end - bounds.start + 1;

    // First, draw vertical course lines and labels
    ctx.beginPath();
    for (var i = 1; i < num_vert; i++) {
        ctx.moveTo(width * i, 0);
        ctx.lineTo(width * i, canvas.height);
        ctx.fillText(bounds.days.charAt(i - 1), width * i + 1, 1);
    }

    // Then, draw vertical course lines and labels
    for (i = 1; i < num_hori; i++) {
        ctx.moveTo(0, height * i);
        ctx.lineTo(canvas.width, height * i);
        ctx.fillText(date_to_string(bounds.start + i), 1, height * i + 1);
    }
    ctx.closePath();
    ctx.stroke();
}

function draw_course(canvas, ctx, course, bounds) {
    for (var idx = 0, days = course.days.length; idx < days; idx++) {
        // Draw a different rectangle for each day
        var rect_idx = bounds.days.search(course.days.charAt(idx));
        var x = (rect_idx + 1) * bounds.width;
        var y = ((course.start - bounds.start + 1) * bounds.height);
        var width = bounds.width;
        var height = course.length * bounds.height;

        // Add text for each day as well
        ctx.fillRect(x, y, width, height);
        var rect_color = ctx.fillStyle;
        ctx.fillStyle = "rgb(0,0,0)";
        var text_width = ctx.measureText(course.course).width;
        // Temporary text wrapping measure... kinda sucks still though
        if (text_width >= bounds.width - 1) {
            var words = course.course.split(" ");
            for (var i = 0, j = words.length; i < j; i++) {
                ctx.fillText(words[i], x + 1, y + 1 + (bounds.height * i));
            }
        }
        else {
            ctx.fillText(course.course, x + 1, y + 1);
        }
        ctx.fillStyle = rect_color;
    }
}

function draw_courses(canvas, ctx, courses, bounds) {
    for (var i = 0, j = courses.length; i < j; i++) {
        console.log("Drawing course", courses[i]);
        var blue_color = Math.floor(((200 / j) * i) + 30);
        var green_color = Math.floor(100 * (i % 3));
        ctx.fillStyle = ("rgba(0, " + green_color.toString() + ", " +
                         blue_color.toString() + ", 0.5)");
        draw_course(canvas, ctx, courses[i], bounds);
    }
}

function draw() {
    var canvas = document.getElementById("calendar");
    if (!canvas.getContext) {
        console.log("Canvas unsupported in browser!");
        return;
    }
    var ctx = canvas.getContext("2d");
    var courses = test_calendar_weekend;

    // Compute data needed to draw the scale and whatnot.
    var bounds = find_range(courses);
    bounds.width = canvas.width / (bounds.days.length + 1);
    bounds.height = canvas.height / (bounds.end - bounds.start + 1);

    var font_size = Math.min(12, Math.floor(bounds.height) - 4);
    ctx.font = "bold " + font_size + "px sans-serif";
    ctx.textBaseline = "top";
    ctx.textAlign = "left";

    // First, draw the grid
    draw_grid(canvas, ctx, bounds);

    // Then, draw courses
    console.log("Drawing courses");
    draw_courses(canvas, ctx, courses, bounds);
}
