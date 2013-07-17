#!/usr/bin/python

import sys

sys.path.append('db')
sys.path.append('kingdomimg')
sys.path.append('leaders')
sys.path.append('logparse')
sys.path.append('logsearch')
sys.path.append('automatch')

from ..model import dbmgr

def test_search():
    p = {}
    p['p1name'] = 'Andrew Iannaccone'
    p['p2name'] = 'SheCantSayNo'
    p['p1score'] = None
    p['bot'] = False 
    p['guest'] = False
    p['rating'] = 'pro+'
    p['pcount'] = None
    p['colony'] = None
    p['shelters'] = None
    p['quit'] = None
    p['minturns'] = 1
    p['maxturns'] = 30
    p['supply'] = None
    p['casesensitive'] = False
    p['startdate'] = None
    p['enddate'] = None
    p['limit'] = 30
    p['offset'] = None

    for r in dbmgr.search_log_filenames(p):
        print(r)

    for r in dbmgr.search_scores(p):
        print(r)

    print(dbmgr.summarize_scores('Andrew Iannaccone', p))

if __name__ == '__main__':
    generate_ratings()
