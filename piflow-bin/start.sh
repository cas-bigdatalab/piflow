#!/bin/bash
function pstart()
{
        nohup java -cp ./lib/piflow-server-0.9.jar cn.piflow.api.Main -Djava.awt.headless=true -Djava.library.path=/usr/local/lib64/python3.6/site-packages/jep/ > ./logs/piflow.log 2>&1 &
}
pstart
echo "PiFlow is running! check log in logs/piflow.log"
