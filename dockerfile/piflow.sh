#!/bin/bash

#echo "--------------------Add master to hosts--------------------"
#ipaddr=`ip addr|grep inet|grep -v 127.0.0.1|grep -v inet6|awk '{print $2}'|sed 's/\/.*$//'`
#echo $ipaddr " master"  >> /etc/hosts
#echo $ipaddr " master"

#echo "--------------------Start SSH Server---------------------"
service ssh start

echo "--------------------Start Hadoop---------------------------"
mkdir -p /var/run/hadoop-hdfs
hadoop namenode -format
/opt/hadoop-2.6.0/sbin/start-all.sh

echo "--------------------Start Spark----------------------------"
/opt/spark-2.2.0-bin-hadoop2.6/sbin/start-all.sh

#echo "--------------------Start Mysql Server---------------------"
#chown -R mysql:mysql /var/lib/mysql
#service mysql start

echo "--------------------Start PiFlow---------------------------"
echo "SPARK_HOME:" $SPARK_HOME
source /etc/profile
echo "HOST_IP" $HOST_IP
cd /opt/piflow/piflow-server-v0.9; ./start.sh
cd /opt/piflow/piflow-web-v0.9; ./start.sh
echo "http://${HOST_IP}:6001/"

echo "SPARK_HOME:" $SPARK_HOME
source /etc/profile

