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
    { course: "00-000 CC",
      start: 20,
      length: 3,
      days: "F" },
    { course: "99-999 AA",
      start: 20,
      length: 10,
      days: "MWF" },
    { course: "11-111 QQ",
      start: 20,
      length: 5,
      days: "F" }
];

var test_calendar_mid_conflict = [
    { course: "18-100 A",
      start: 17,
      length: 4,
      days: "F" },
    { course: "18-100 B",
      start: 18,
      length: 4,
      days: "F" },
    { course: "99-999 W",
      start: 20,
      length: 10,
      days: "MWF" }
];
