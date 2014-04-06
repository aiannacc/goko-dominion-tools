#!/usr/bin/python

import postgresql

from gdt.model import db_manager

_con = postgresql.open(user='ai', host='localhost', database='goko')


def correct_pnames(old, new):
    print('Updating      ', old, '          ', new)
    _con.prepare("""UPDATE presult
                       SET pname=$1
                     WHERE pname=$2""")(new, old)


# Find and fix player names that were incorrected decoded as ISO-8859-1 when
# they were actually UTF-8
# TODO: Recalculate the leaderboard using the corrected player names
# TODO: Fix or re-download the log files themselves
# NOTE: There are still some player names that are garbled.  I don't know why.
if __name__ == '__main__':
    for (row) in _con.prepare("""
                SELECT DISTINCT(pname)
                  FROM presult""")():
        x = row[0]
        try:
            y = x.encode('iso-8859-1').decode('utf-8')
            if x != y:
                correct_pnames(x, y)
        except:
            pass
