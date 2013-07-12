#!/usr/bin/env python

import re
import sys
import os
import signal
import time
import datetime
import trueskill

sys.path.append('../db')
import dbmgr


class ts_system:
    def __init__(self):
        self.ratings = {}

if __name__ == '__main__':
    start = datetime.strptime(sysvargs[1])
    print(dbmgr.fetch_winners_losers())
