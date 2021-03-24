![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-logo2.png)  
[![GitHub releases](https://img.shields.io/github/release/cas-bigdatalab/piflow.svg)](https://github.com/cas-bigdatalab/piflow/releases)
[![GitHub stars](https://img.shields.io/github/stars/cas-bigdatalab/piflow.svg)](https://github.com/cas-bigdatalab/piflow/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/cas-bigdatalab/piflow.svg)](https://github.com/cas-bigdatalab/piflow/network)
[![GitHub downloads](https://img.shields.io/github/downloads/cas-bigdatalab/piflow/total.svg)](https://github.com/cas-bigdatalab/piflow/releases)
[![GitHub issues](https://img.shields.io/github/issues/cas-bigdatalab/piflow.svg)](https://github.com/cas-bigdatalab/piflow/issues)


πFlow is an easy to use, powerful big data pipeline system.
Try PiFlow v0.6 with: http://piflow.cstcloud.cn/piflow-web/
## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Requirements](#requirements)
- [Getting Started](#getting-started)
- [PiFlow Docker](#docker-started)
- [Use Interface](#use-interface)
- [Contact Us](#contact-us)

## Features

- Easy to use
  - provide a WYSIWYG web interface to configure data flow
  - monitor data flow status
  - check the logs of data flow
  - provide checkpoints
- Strong scalability:
  - Support customized development of data processing components
- Superior performance
  - based on distributed computing engine Spark 
- Powerful
  - 100+ data processing components available
  - include spark、mllib、hadoop、hive、hbase、solr、redis、memcache、elasticSearch、jdbc、mongodb、http、ftp、xml、csv、json，etc.

## Architecture
![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/architecture.png) 
## Requirements
* JDK 1.8 
* Scala-2.11.8
* Apache Maven 3.1.0 or newer  
* Spark-2.1.0、 Spark-2.2.0、 Spark-2.3.0
* Hadoop-2.6.0

## Getting Started

### To Build:  
- `install external package`
          
          mvn install:install-file -Dfile=/../piflow/piflow-bundle/lib/spark-xml_2.11-0.4.2.jar -DgroupId=com.databricks -DartifactId=spark-xml_2.11 -Dversion=0.4.2 -Dpackaging=jar
          mvn install:install-file -Dfile=/../piflow/piflow-bundle/lib/java_memcached-release_2.6.6.jar -DgroupId=com.memcached -DartifactId=java_memcached-release -Dversion=2.6.6 -Dpackaging=jar
          mvn install:install-file -Dfile=/../piflow/piflow-bundle/lib/ojdbc6-11.2.0.3.jar -DgroupId=oracle -DartifactId=ojdbc6 -Dversion=11.2.0.3 -Dpackaging=jar
          mvn install:install-file -Dfile=/../piflow/piflow-bundle/lib/edtftpj.jar -DgroupId=ftpClient -DartifactId=edtftp -Dversion=1.0.0 -Dpackaging=jar
          

- `mvn clean package -Dmaven.test.skip=true`

          [INFO] Replacing original artifact with shaded artifact.
          [INFO] Reactor Summary:
          [INFO]
          [INFO] piflow-project ..................................... SUCCESS [  4.369 s]
          [INFO] piflow-core ........................................ SUCCESS [01:23 min]
          [INFO] piflow-configure ................................... SUCCESS [ 12.418 s]
          [INFO] piflow-bundle ...................................... SUCCESS [02:15 min]
          [INFO] piflow-server ...................................... SUCCESS [02:05 min]
          [INFO] ------------------------------------------------------------------------
          [INFO] BUILD SUCCESS
          [INFO] ------------------------------------------------------------------------
          [INFO] Total time: 06:01 min
          [INFO] Finished at: 2020-05-21T15:22:58+08:00
          [INFO] Final Memory: 118M/691M
          [INFO] ------------------------------------------------------------------------

### Run Piflow Server：

- `run piflow server on Intellij`:   
  - download piflow: git clone https://github.com/cas-bigdatalab/piflow.git
  - import piflow into Intellij
  - edit config.properties file
  - build piflow to generate piflow jar:   
    - Edit Configurations --> Add New Configuration --> Maven  
    - Name: package
    - Command line: clean package -Dmaven.test.skip=true -X  
    - run 'package' (piflow jar file will be built in ../piflow/piflow-server/target/piflow-server-0.9.jar)  
    
  - run HttpService:   
    - Edit Configurations --> Add New Configuration --> Application  
    - Name: HttpService
    - Main class : cn.piflow.api.Main  
    - Environment Variable: SPARK_HOME=/opt/spark-2.2.0-bin-hadoop2.6(change the path to your spark home)  
    - run 'HttpService'
  
  - test HttpService:   
    - run /../piflow/piflow-server/src/main/scala/cn/piflow/api/HTTPClientStartMockDataFlow.scala
    - change the piflow server ip and port to your configure
  
  
- `run piflow server by release version`:
  - download piflow.tar.gz:   
    https://github.com/cas-bigdatalab/piflow/releases/download/v0.9/piflow-server-v0.9.tar.gz  
    https://github.com/cas-bigdatalab/piflow/releases/download/v0.8/piflow-server-v0.8.tar.gz  
    https://github.com/cas-bigdatalab/piflow/releases/download/v0.7/piflow-server-v0.7.tar.gz  
    https://github.com/cas-bigdatalab/piflow/releases/download/v0.6/piflow-server-v0.6.tar.gz   
    https://github.com/cas-bigdatalab/piflow/releases/download/v0.5/piflow.tar.gz    
     
      
    
    
  - unzip piflow.tar.gz:  
    tar -zxvf piflow.tar.gz
    
  - edit config.properties  
  
  - run start.sh、stop.sh、 restart.sh、 status.sh  
  
  - test piflow server
    - set PIFLOW_HOME  
      - vim /etc/profile  
        export PIFLOW_HOME=/yourPiflowPath/bin  
      	export PATH=$PATH:$PIFLOW_HOME/bin  
      - command   
        piflow flow start example/mockDataFlow.json  
        piflow flow stop appID  
        piflow flow info appID  
        piflow flow log appID  
      
        piflow flowGroup start example/mockDataGroup.json  
        piflow flowGroup stop groupId  
        piflow flowGroup info groupId  
        
- `how to configure config.properties`
     
      #spark and yarn config
      spark.master=yarn
      spark.deploy.mode=cluster
      
      #hdfs default file system
      fs.defaultFS=hdfs://10.0.86.191:9000
      
      #yarn resourcemanager.hostname
      yarn.resourcemanager.hostname=10.0.86.191
      
      #if you want to use hive, set hive metastore uris
      #hive.metastore.uris=thrift://10.0.88.71:9083
      
      #show data in log, set 0 if you do not want to show data in logs
      data.show=10
      
      #server port
      server.port=8002
      
      #h2db port
      h2.port=50002

  
### Run Piflow Web：
  - Visit address, download the corresponding *.tar.gz file, and modify the corresponding configuration file（`The version must be consistent with piflow-server`） 
    - https://github.com/cas-bigdatalab/piflow-web/releases/tag/v0.9  
    - https://github.com/cas-bigdatalab/piflow-web/releases/tag/v0.8
    - https://github.com/cas-bigdatalab/piflow-web/releases/tag/v0.7
    - https://github.com/cas-bigdatalab/piflow-web/releases/tag/v0.6
    - https://github.com/cas-bigdatalab/piflow-web/releases/tag/v0.5
  
### Restful API：

- flow json
  <details>
    <summary>flow example</summary>
    <pre>
      <code>
        {
  "flow": {
    "name": "MockData",
    "executorMemory": "1g",
    "executorNumber": "1",
    "uuid": "8a80d63f720cdd2301723b7461d92600",
    "paths": [
      {
        "inport": "",
        "from": "MockData",
        "to": "ShowData",
        "outport": ""
      }
    ],
    "executorCores": "1",
    "driverMemory": "1g",
    "stops": [
      {
        "name": "MockData",
        "bundle": "cn.piflow.bundle.common.MockData",
        "uuid": "8a80d63f720cdd2301723b7461d92604",
        "properties": {
          "schema": "title:String, author:String, age:Int",
          "count": "10"
        },
        "customizedProperties": {

        }
      },
      {
        "name": "ShowData",
        "bundle": "cn.piflow.bundle.external.ShowData",
        "uuid": "8a80d63f720cdd2301723b7461d92602",
        "properties": {
          "showNumber": "5"
        },
        "customizedProperties": {

        }
      }
    ]
  }
}</code>
    </pre>
  </details>
- CURL POST：
  - curl -0 -X POST http://10.0.86.191:8002/flow/start -H "Content-type: application/json" -d 'this is your flow json'
  
- Command line： 
  - set PIFLOW_HOME  
    vim /etc/profile  
  	export PIFLOW_HOME=/yourPiflowPath/piflow-bin  
    export PATH=$PATH:$PIFLOW_HOME/bin  

  - command example  
    piflow flow start yourFlow.json  
    piflow flow stop appID  
    piflow flow info appID  
    piflow flow log appID  

    piflow flowGroup start yourFlowGroup.json  
    piflow flowGroup stop groupId  
    piflow flowGroup info groupId  
    
## docker-started  
  - pull piflow images  
    docker pull registry.cn-hangzhou.aliyuncs.com/cnic_piflow/piflow:v0.9.1  
    
  - show docker images  
    docker images
    
  - run a container with  piflow imageID ， all services run automatically  
    docker run -h master -itd --env HOST_IP=\*.\*.\*.\* --name piflow-v0.9.1 -p 6001:6001 -p 6002:6002  [imageID]  
    
  - please visit "HOST_IP:6001", it may take a while  
  
  - if somethings goes wrong,  all the application are in /opt  folder  
  
## use-interface
- `Login`:

  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-login.png)
  
- `Dashboard`:

  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/dashboard.png)
  
- `Flow list`:

  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-flowlist.png)
  
- `Create flow`:

  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-createflow.png)
  
- `Configure flow`:

  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-flowconfig.png)
  
- `Load flow`:

  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-loadflow.png)
  
- `Monitor flow`:  

  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-monitor.png)

- `Flow logs`:

  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-log.png)
  
- `Group list`:  

  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-group-list.png)

- `Configure group`:

  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-configure-group.png)

- `Monitor group`:

  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-monitor-group.png)

- `Process List`:

  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-processlist.png)
  
- `Template List`:

  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-templatelist.png)

- `DataSource List`:

  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-datasourcelist.png)
  
- `Schedule List`:

  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-schedulelist.png)
  
- `StopHub List`:

  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-stophublist.png)
  
## Contact Us
- Name:吴老师  
- Mobile Phone：18910263390  
- WeChat：18910263390  
- Email: wzs@cnic.cn  
- QQ Group：1003489545  
  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/PiFlowUserGroup_QQ.jpeg)
- WeChat group is valid for 7 days
  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/PiFlowUserGroup.png)



