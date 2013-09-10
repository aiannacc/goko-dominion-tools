sudo kill -9 `ps -ef | grep python | grep start_servers.py | perl -pe s/^S*s*(S*).*//` && sudo nohup ./start_servers.py 80 8888 443 &
