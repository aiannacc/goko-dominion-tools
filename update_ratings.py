#!/usr/bin/python

import gdt.model.db_manager as db_manager
import gdt.ratings.gdt_trueskill as ts

count = -1
while count != 0:
  x = db_manager.get_last_rated_game()
  if x:
    (t, l) = x
  else:
    (t, l) = (None, None)
  count = ts.record_ratings(100, t, l, ts.isodominion_env)
