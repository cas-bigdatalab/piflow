1.maven error
apt-get install maven
mvn install:install-file -Dfile=/opt/project/piflow/piflow-bundle/lib/spark-xml_2.11-0.4.2.jar -DgroupId=com.databricks -DartifactId=spark-xml_2.11 -Dversion=0.4.2 -Dpackaging=jar

2.packaging

clean package -Dmaven.test.skip=true -U

