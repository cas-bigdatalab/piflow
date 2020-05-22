1.maven error
  apt-get install maven
  mvn install:install-file -Dfile=/opt/project/piflow/piflow-bundle/lib/spark-xml_2.11-0.4.2.jar -DgroupId=com.databricks -DartifactId=spark-xml_2.11 -Dversion=0.4.2 -Dpackaging=jar
  mvn install:install-file -Dfile=/opt/project/piflow/piflow-bundle/lib/java_memcached-release_2.6.6.jar -DgroupId=com.memcached -DartifactId=java_memcached-release -Dversion=2.6.6 -Dpackaging=jar
  mvn install:install-file -Dfile=/opt/project/piflow/piflow-bundle/lib/ojdbc6-11.2.0.3.jar -DgroupId=oracle -DartifactId=ojdbc6 -Dversion=11.2.0.3 -Dpackaging=jar
  mvn install:install-file -Dfile=/opt/project/piflow/piflow-bundle/lib/edtftpj.jar -DgroupId=ftpClient -DartifactId=edtftp -Dversion=1.0.0 -Dpackaging=jar

2.Packaging by Intellij
  1)Edit Configurations --> add Maven
    Command line: clean package -Dmaven.test.skip=true -X
  2)Build piflow-server-0.9.jar

3.run main class in Intellij


  1)Edit Configurations --> Application
    Main class: cn.piflow.api.Main
    Environment Variable: SPARK_HOME=/opt/spark-2.2.0-bin-hadoop2.6;


