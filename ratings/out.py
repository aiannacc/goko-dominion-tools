#!/usr/bin/env python

# Connect to the "dominionlogs" database
import pymysql,csv
db  = pymysql.connect(db='dominionlogs',charset='utf8')
cur = db.cursor()

w = csv.writer(open('out.csv','wt'))

cur.execute('SELECT * FROM matches')
w.writerows(cur.fetchall())
