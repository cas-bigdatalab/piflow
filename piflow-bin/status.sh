#!/bin/bash
#ps term
function check_status()
{
        [ ${#} -eq 0 ] && echo "usage: $FUNCNAME STRING" && return 0
        local pid 
        pid=$(ps ax | grep "$1" | grep -v grep | awk '{ print $1 }')
	if [[ "" -ne $pid ]]
	then
		echo "server is Running!"
		port=$(netstat -nltp | grep $pid | awk '{print $4}')
		echo "$port"
	else
		echo "Server is Stopped!"
	fi
}
#ps grep
#ps aux | grep "piflow.api.Main"| grep -v 'grep'
check_status piflow.api.Main 
