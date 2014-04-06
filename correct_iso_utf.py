#!/usr/bin/python

import postgresql

from gdt.model import db_manager

_con = postgresql.open(user='ai', host='localhost', database='goko')


def correct_pnames(old, new):
    print('Updating      ', old, '          ', new)
    _con.prepare("""UPDATE presult
                       SET pname=$1
                     WHERE pname=$2""")(new, old)

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
