1.maven error
apt-get install maven
mvn install:install-file -Dfile=/opt/project/piflow/piflow-bundle/lib/spark-xml_2.11-0.4.2.jar -DgroupId=com.databricks -DartifactId=spark-xml_2.11 -Dversion=0.4.2 -Dpackaging=jar

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


