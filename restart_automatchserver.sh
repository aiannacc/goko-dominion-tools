#!/bin/bash

pid=`ps -ef | grep python | grep start_servers.py | perl -pe 's/^\S*\s*(\S*).*/$1/'`
echo $pid
sudo kill -9 $pid && sudo nohup ./start_servers.py 80 8888 443 &
