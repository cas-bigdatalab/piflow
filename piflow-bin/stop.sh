#!/bin/bash
#ps term
function psterm()
{
        [ ${#} -eq 0 ] && echo "usage: $FUNCNAME STRING" && return 0
        local pid 
        pid=$(ps ax | grep "$1" | grep -v grep | awk '{ print $1 }')
        #echo -e "terminating '$1' / process(es):\n$pid"
        kill -9 $pid 2 >/dev/null
}
#ps grep
#ps aux | grep "piflow.api.Main"| grep -v 'grep'
psterm piflow.api.Main 2>/dev/null 
echo "Stop OK!"
