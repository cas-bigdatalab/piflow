#!/bin/bash
#java -cp piflow-server-0.9.jar:./classpath/piflow-external.jar cn.piflow.api.Main
#java -cp piflow-server-0.9.jar:./classpath/* cn.piflow.api.Main
nohup java -cp ./lib/piflow-server-0.9.jar:./classpath/* cn.piflow.api.Main > ./logs/piflow.log 2>&1 &
echo "check log in piflow.log"

