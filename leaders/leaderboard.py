#!/usr/bin/env python

url = "http://www.goko.com/games/Dominion/leaders"

import time
import re
import traceback
import sys
from tornado.httpclient import *
from bs4 import BeautifulSoup
from datetime import datetime

sys.path.append('../db')
import dbmgr

while True:
    try:
        response = HTTPClient().fetch(url)
        soup = BeautifulSoup(response.body)
        leaderboard = soup.find('table', class_="leaders-table")
        now = datetime.now()

        trpr = []
        n = 0
        for entry in leaderboard.find_all('tr'):
            player = entry.find(class_='table-item-name')
            if (not player is None):
                try:
                    pname = entry.find(class_='table-item-name').text
                    rank = int(entry.find(class_='table-item-rank').text)
                    rating = int(entry.find(class_='table-item-points').text)
                    trpr.append((now, rank, pname, rating))
                    n += 1
                except:
                    pass
        dbmgr.insert_leaderboard(trpr)
        print('Parsed %d entries at %s' % (n, now))
    except:
        pass

    time.sleep(60)
