#!/bin/bash

. "/opt/spark/bin/load-spark-env.sh"

if [ "$SPARK_WORKLOAD" == "master" ];
then

export SPARK_MASTER_HOST=127.0.0.1

cd /opt/spark/bin && ./spark-class org.apache.spark.deploy.master.Master --ip $SPARK_MASTER_HOST --port $SPARK_MASTER_PORT --webui-port $SPARK_MASTER_WEBUI_PORT >> $SPARK_MASTER_LOG

fi


#集群配置,需要再docker-compose文件中加入其他两个节点的配置 
# elif [ "$SPARK_WORKLOAD" == "worker" ];
# then

# cd /opt/spark/bin && ./spark-class org.apache.spark.deploy.worker.Worker --webui-port $SPARK_WORKER_WEBUI_PORT $SPARK_MASTER >> $SPARK_WORKER_LOG

# elif [ "$SPARK_WORKLOAD" == "submit" ];
# then
#     echo "SPARK SUBMIT"
# else
#     echo "Undefined Workload Type $SPARK_WORKLOAD, must specify: master, worker, submit"
# fi
