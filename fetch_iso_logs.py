import datetime
import time
import requests

day = datetime.datetime.strptime('20130330', '%Y%m%d')
n_failure = 0
n_success = 0

while n_success == 0 or n_failure < 30:
    datestr = day.strftime('%Y%m%d')

    dayurl = 'https://s3.amazonaws.com/static.councilroom.mccllstr.com/'\
        + 'scrape_data/%s.all.tar.bz2' % datestr
    print(dayurl)
    r = requests.get(dayurl)
    success = r.status_code == 200

    if success:
        #log_file = '/home/ai/test/logs/%s.all.tar.bz2' % datestr
        log_file = '/mnt/raid/media/dominion-iso/logs/%s.all.tar.bz2' % datestr
        f = open(log_file, 'wb')
        f.write(r.content)
        f.close()
        n_failure = 0
        n_success += 1
    else:
        print('No logs for %s' % datestr)

    day = day + datetime.timedelta(days=-1)
    time.sleep(0.1)
