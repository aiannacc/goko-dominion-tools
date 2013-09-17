#!/bin/bash

pid=`ps -ef | grep python | grep start_servers.py | perl -pe 's/^\S*\s*(\S*).*/$1/'`
echo $pid
if [ -n "$pid" ]
then
    sudo kill -9 $pid && sudo nohup python start_logserver.py 80 &
else 
    sudo nohup python start_logserver.py 80 &
fi
