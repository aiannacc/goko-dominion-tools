pkill -9 python
ps -efl | grep python
sleep 1
nohup python start_automatchserver.py 443 &
sleep 1
nohup python start_extserver.py 8888 &
sleep 1
nohup python start_logserver.py 80 &
sleep 1
nohup python start_logwatcher.py &
ps -efl | grep python
