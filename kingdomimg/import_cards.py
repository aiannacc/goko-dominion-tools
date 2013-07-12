#!/usr/bin/env python

import csv,sys

sys.path.append('../db')
import dbmgr

reader = csv.reader(open('cardurls.txt'))
for row in reader:
    (card,url) = row
    dbmgr.insert_card_url(card,url)
