1.maven error
apt-get install maven
mvn install:install-file -Dfile=/root/Desktop/dblp/piflow-bundle/lib/spark-xml_2.11-0.4.2.jar -DgroupId=com.databricks -DartifactId=spark-xml_2.11 -Dversion=0.4.2 -Dpackaging=jar
mvn install:install-file -Dfile=/root/Desktop/dblp/piflow-bundle/lib/java_memcached-release_2.6.6.jar -DgroupId=com.memcached -DartifactId=java_memcached-release -Dversion=2.6.6 -Dpackaging=jar
mvn install:install-file -Dfile=/root/Desktop/dblp/piflow-bundle/lib/ojdbc6.jar -DgroupId=jdbc_oracle -DartifactId=ojdbc -Dversion=6.0.0 -Dpackaging=jar
mvn install:install-file -Dfile=/root/Desktop/dblp/piflow-bundle/lib/edtftpj.jar -DgroupId=ftpClient -DartifactId=edtftp -Dversion=1.0.0 -Dpackaging=jar

2.packaging

clean package -Dmaven.test.skip=true -U

3.set SPARK_HOME in Configurations
  Edit Configurations --> Application(HttpService) --> Configurations --> Environment Variable

4. yarn log aggregation
  Edit yarn-site.xml, add the following content
     <property>
      <name>yarn.log-aggregation-enable</name>
      <value>true</value>
     </property>

     <property>
      <name>yarn.nodemanager.log-aggregation.debug-enabled</name>
      <value>true</value>
     </property>

     <property>
      <name>yarn.nodemanager.log-aggregation.roll-monitoring-interval-seconds</name>
      <value>3600</value>
     </property>

5.kafka related jars are needed to put on the spark cluster
    spark-streaming-kafka-0-10_2.11-2.1.0.jar
    kafka_2.11-2.1.1.jar
    kafka-clients-2.1.1.jar

    start kafka server:     ./bin/kafka-server-start.sh -daemon config/server.properties
    stop kafka server:      ./bin/kafka-server-stop.sh
    start kafka producer:   ./bin/kafka-console-producer.sh --broker-list master:9092,slave1:9092,slave2:9092 --topic streaming
    start kafka consumer:   ./bin/kafka-console-consumer.sh --zookeeper master:2181,slave1:2181,slave2:2181 --topic streaming
    list topics:
                            ./bin/kafka-topics.sh --list --zookeeper master:2181,slave1:2181,slave2:2181
                            ./bin/kafka-topics.sh --list --zookeeper master:2181,slave1:2181,slave2:2181
    create topics:
                            ./bin/kafka-topics.sh --create --zookeeper master:2181,slave1:2181,slave2:2181 --replication-factor 3 --partictions 3 --topic newTopic


6.flume related jars are needed to put on the spark cluster
    spark-streaming-flume_2.11-2.1.0.jar

    start flume agent: bin/flume-ng agent -n streamingAgent -c conf -f conf/streaming.conf -Dflume.root.logger=INFO,console

7.socket text stream

    nc -lk 9999

