#!/bin/bash
function pstart()
{
	#java -cp piflow-server-0.9.jar:./classpath/piflow-external.jar cn.piflow.api.Main
	#java -cp piflow-server-0.9.jar:./classpath/* cn.piflow.api.Main
        classpathDir="./classpath"
	if [ ! -e ./classpath/*.jar ];
	then
		echo "No Customized Stop!"
		nohup java -cp ./lib/piflow-server-0.9.jar cn.piflow.api.Main -Djava.awt.headless=true > ./logs/piflow.log 2>&1 &
	else
		echo "Load Customized Stop from classpath"
		nohup java -cp ./lib/piflow-server-0.9.jar:./classpath/* cn.piflow.api.Main -Djava.awt.headless=true > ./logs/piflow.log 2>&1 &
	fi
			 
	#nohup java -cp ./lib/piflow-server-0.9.jar cn.piflow.api.Main -Djava.awt.headless=true > ./logs/piflow.log 2>&1 &
}
pstart
echo "PiFlow is running! check log in logs/piflow.log"
