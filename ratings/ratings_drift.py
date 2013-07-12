#!/usr/bin/env python

import hashlib, sys, os, re
from datetime import datetime

# Connect to the "dominionlogs" database
import pymysql
db  = pymysql.connect(db='dominionlogs',charset='utf8')
cur = db.cursor()

qry = 'SELECT * from ratings order by time desc limit %d' % (100*24*60*3)
cur.execute(qry)

last = {}
changes = {}
rchanges = {}
rchangesn = {}
for r in cur.fetchall():
    (time,rank,pname,rating) = r
    if not pname in last:
        last[pname] = rating
        changes[pname] = {}
    else:
        changes[pname][time] = last[pname] - rating
        if not time in rchanges:
            rchanges[time] = []
            rchangesn[time] = []
        else:
            rchanges[time].append(last[pname] - rating)
            rchangesn[time].append(pname)
        last[pname] = rating

for p in changes:
    for t in changes[p]:
        timestr = t.strftime('%H:%M')
        print(timestr,changes[p][t])

for t in sorted(rchanges):
    timestr = t.strftime('%Y-%m-%d %H:%M')
    if len(rchanges[t]) > 50:
        print(timestr, sum(rchanges[t])/len(rchanges[t]))

        for i in range(len(rchanges[t])):
            print(rchangesn[t][i], rchanges[t][i])

