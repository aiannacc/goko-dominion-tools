#!/bin/bash

pid=`ps -ef | grep python | grep start_automatchserver.py | perl -pe 's/^\S*\s*(\S*).*/$1/'`
echo $pid
if [ -n "$pid" ]
then
    sudo kill -9 $pid && sudo nohup python start_automatchserver.py 443 &
else 
    sudo nohup python start_automatchserver.py 443 &
fi
