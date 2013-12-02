from gen_schedule import gen_schedule, Course


os = Course(12, {1 : ('', 0, 0, {'A': ('MWF', 1030, 1120)})},
            "15410", float('inf'))
pic = Course(10, {1 : ('TR', 900, 1020, {'A': ('WF', 930, 1020),
                                         'B': ('WF', 1030, 1120),
                                         'C': ('WF', 1130, 1220),
                                         'D': ('WF', 1230, 1320),
                                         'E': ('WF', 1330, 1420),
                                         'F': ('WF', 1430, 1520),
                                         'G': ('WF', 1530, 1620),
                                         'H': ('WF', 1630, 1720)})},
            "15122",
            37.5)
concepts = Course(10, {1: ('MWF', 1330, 1420, {'A': ('TR', 1230, 1320),
                                               'B': ('TR', 1330, 1420),
                                               'C': ('TR', 1430, 1520),
                                               'D': ('TR', 1530, 1620),
                                               'E': ('TR', 1630, 1720)}),
                       2: ('MWF', 1530, 1620, {'F': ('TR', 1030, 1120),
                                               'G': ('TR', 1230, 1320),
                                               'H': ('TR', 1330, 1420),
                                               'I': ('TR', 1530, 1620)})},
                 "21127",
                 35)

proof = Course(9, {1: ('', 0, 0, {'A': ('TR', 1500, 1620)})}, "80411", 50)

res = gen_schedule([os, pic, concepts, proof], min_units=20)
for x in res:
  print x