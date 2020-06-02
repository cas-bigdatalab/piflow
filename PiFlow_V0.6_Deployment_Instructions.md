

# 1.Piflow Server

## 1.1 环境要求

1.已部署Spark2，Hadoop，Yarn，Hive

2.JDK1.8

3.scala 2.11.8

## 1.2 安装文件

下载安装文件：

https://github.com/cas-bigdatalab/piflow/releases/download/v0.6/piflow-server-v0.6.tar.gz

将piflow-server-v0.6.tar.gz解压，如下图所示：

![](http://image-picgo.test.upcdn.net/img/20200602135034.png)

其中，classpath为用户自定开发组件Stop放置路径；config.properties为配置文件；lib为piflowServer所需jar包；piflow-server-0.9.jar为piflowServer本身jar包；start.sh为piflowServer启动脚本。

Config.properties配置文件如下;

 ```properties
#server Ip and Port
server.ip=10.0.88.70
server.port=8002

#Spark master and deploy mode
spark.master=yarn
spark.deploy.mode=cluster

#yarn related configurations
yarn.resourcemanager.hostname=10.0.88.70
yarn.resourcemanager.address=10.0.88.70:8032
yarn.access.namenode=hdfs://10.0.88.70:9000
yarn.stagingDir=hdfs://10.0.88.70:9000/tmp/
yarn.jars=hdfs://10.0.88.70:9000/user/spark/share/lib/*.jar
yarn.url=http://10.0.88.70:8088/ws/v1/cluster/apps/

#hive metaStore uris
hive.metastore.uris=thrift://10.0.88.71:9083

#piflow server jar folder, please change this parameter to your path
piflow.bundle=/data/piflow/piflow-server-v0.6/lib/piflow-server-0.9.jar

#hdfs path for checkpoint、debug、increment，please create these folders first
checkpoint.path=hdfs://10.0.88.70:9000/user/piflow/checkpoints/
debug.path=hdfs://10.0.88.70:9000/user/piflow/debug/
increment.path=hdfs://10.0.88.70:9000/user/piflow/increment/

#set 0 if you don not want to show data in log
data.show=10

#h2 db port
h2.port=50002

 ```





## 1.3 环境配置

配置集群的环境变量（自定义按需配置）

```properties
export JAVA_HOME=/opt/java
export JRE_HOME=/opt/java/jre
export CLASSPATH=.:$JAVA_HOME/lib:$JRE_HOME/lib:$CLASSPATH
export PATH=$JAVA_HOME/bin:$JRE_HOME/bin:$PATH

export HADOOP_HOME=/opt/hadoop-2.6.0
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin

export HIVE_HOME=/opt/apache-hive-2.3.6-bin
export PATH=$PATH:$HIVE_HOME/bin

export SPARK_HOME=/opt/spark-2.1.0-bin-hadoop2.6
export PATH=$PATH:$SPARK_HOME/bin

export SCALA_HOME=/opt/scala-2.11.8
export PATH=$PATH:$SCALA_HOME/bin

```



## 1.4 运行

![](http://image-picgo.test.upcdn.net/img/20200602135103.png)
 

```
 ./start.sh   
```



 

# 2.Piflow Web

## 1.1 环境要求

1.MYSQL5.7

2.JDK1.8

## 1.2 项目部署

下载安装文件：

https://github.com/cas-bigdatalab/piflow-web/releases/download/v0.6/piflow-web-v0.6.tar.gz

将piflow-web-v0.6.tar.gz解压，如下图所示：

![](http://image-picgo.test.upcdn.net/img/20200602135121.png)

解压后内容说明：

(1)、Piflow-web.jar 为 piflow-web的启动jar包。

(2)、config.properties为配置文件。

(3)、srart.sh 为启动脚本

(4)、stop.sh 为停止脚本

(5)、status.sh 为查看状态脚本

(6)、restart.sh 为重启脚本

(7)、piflowWeb.log 为日志文件

 

config.properties配置文件如下;

```
server.port=6001
server.servlet.session.timeout=3600

syspara.interfaceUrlHead=http://10.0.88.108:8002
syspara.isLoadStop=true
syspara.isIframe=true

# data source
# Basic attributes
spring.datasource.name=dev
spring.datasource.url = jdbc:mysql://10.0.88.109:3306/piflow_web?useUnicode=true&characterEncoding=UTF-8&useSSL=false&allowMultiQueries=true&autoReconnect=true&failOverReadOnly=false
spring.datasource.username=root
spring.datasource.password=123456
# Can not be configured, according to the URL automatic identification, recommended configuration
spring.datasource.driver-class-name=com.mysql.jdbc.Driver

# Log Coordination Standard
logging.level.com.nature.mapper=warn
logging.level.root=warn
logging.level.org.springframework.security=warn
logging.level.org.hibernate.SQL=WARN

```



 

 

运行

```
 cd piflow-web  
 ./start.sh  
```



 

 

访问进行登陆注册：http://serverIp:serverPort/piflow-web/

http://192.168.3.141:6001/piflow-web/

![](http://image-picgo.test.upcdn.net/img/20200602135150.png)
