#!/bin/bash

pid=`ps -ef | grep python | grep start_extserver.py | perl -pe 's/^\S*\s*(\S*).*/$1/'`
echo 'PID: ['$pid']'
if [ -n "$pid" ]
then
    sudo kill -9 $pid && sudo nohup python start_extserver.py 8888 &
else
    sudo nohup python start_extserver.py 8888 &
fi
