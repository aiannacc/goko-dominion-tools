#!/usr/bin/python

import gdt
from gdt.ratings.trueskill import *

count = -1
while count != 0:
  x = db_manager.get_last_rated_game()
  if x:
    (t, l) = x
  else:
    (t, l) = (None, None)
  count = record_ratings(10000, t, l)
