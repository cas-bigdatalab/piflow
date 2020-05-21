![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-logo2.png)  
[![GitHub releases](https://img.shields.io/github/release/cas-bigdatalab/piflow.svg)](https://github.com/cas-bigdatalab/piflow/releases)
[![GitHub stars](https://img.shields.io/github/stars/cas-bigdatalab/piflow.svg)](https://github.com/cas-bigdatalab/piflow/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/cas-bigdatalab/piflow.svg)](https://github.com/cas-bigdatalab/piflow/network)
[![GitHub downloads](https://img.shields.io/github/downloads/cas-bigdatalab/piflow/total.svg)](https://github.com/cas-bigdatalab/piflow/releases)
[![GitHub issues](https://img.shields.io/github/issues/cas-bigdatalab/piflow.svg)](https://github.com/cas-bigdatalab/piflow/issues)
[![GitHub license](https://img.shields.io/github/license/cas-bigdatalab/piflow.svg)](https://github.com/cas-bigdatalab/piflow/blob/master/LICENSE)

πFlow is an easy to use, powerful big data pipeline system.
Try PiFlow v0.6 with: http://piflow.cstcloud.cn/piflow-web/
## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Requirements](#requirements)
- [Getting Started](#getting-started)
- [PiFlow Docker](#docker-started)
- [Use Interface](#use-interface)

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
* Git Client (used during build process by 'bower' plugin)
* Spark-2.1.0、 Spark-2.2.0、 Spark-2.3.0
* Hadoop-2.6.0

## Getting Started

To Build: 
`mvn clean package -Dmaven.test.skip=true`

          [INFO] Replacing original artifact with shaded artifact.
          [INFO] Replacing /opt/project/piflow/piflow-server/target/piflow-server-0.9.jar with /opt/project/piflow/piflow-server/target/piflow-server-0.9-shaded.jar
          [INFO] ------------------------------------------------------------------------
          [INFO] Reactor Summary:
          [INFO] 
          [INFO] piflow-project ..................................... SUCCESS [  4.602 s]
          [INFO] piflow-core ........................................ SUCCESS [ 56.533 s]
          [INFO] piflow-bundle ...................................... SUCCESS [02:15 min]
          [INFO] piflow-server ...................................... SUCCESS [03:01 min]
          [INFO] ------------------------------------------------------------------------
          [INFO] BUILD SUCCESS
          [INFO] ------------------------------------------------------------------------
          [INFO] Total time: 06:18 min
          [INFO] Finished at: 2018-12-24T16:54:16+08:00
          [INFO] Final Memory: 41M/812M
          [INFO] ------------------------------------------------------------------------

To Run Piflow Server：

- `run piflow server on intellij`: 
  - edit config.properties
  - build piflow to generate piflow-server-0.9.jar
  - main class is cn.piflow.api.Main(remember to set SPARK_HOME)
  
- `run piflow server by release version`:
  - download piflow.tar.gz: 
    https://github.com/cas-bigdatalab/piflow/releases/download/v0.5/piflow.tar.gz
    https://github.com/cas-bigdatalab/piflow/releases/download/v0.6/piflow-server-v0.6.tar.gz
    https://github.com/cas-bigdatalab/piflow/releases/download/v0.7/piflow-server-v0.7.tar.gz
    
  - unzip piflow.tar.gz: 
    tar -zxvf piflow.tar.gz
    
  - edit config.properties
  - run start.sh、stop.sh、 restart.sh、 status.sh
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

  
To Run Piflow Web：
  - https://github.com/cas-bigdatalab/piflow-web
  
Use with command line：

- command line
  - flow config example
  
        {
          "flow":{
          "name":"test",
          "uuid":"1234",
          "checkpoint":"Merge",
          "stops":[
          {
            "uuid":"1111",
            "name":"XmlParser",
            "bundle":"cn.piflow.bundle.xml.XmlParser",
            "properties":{
                "xmlpath":"hdfs://10.0.86.89:9000/xjzhu/dblp.mini.xml",
                "rowTag":"phdthesis"
            }
          },
          {
            "uuid":"2222",
            "name":"SelectField",
            "bundle":"cn.piflow.bundle.common.SelectField",
            "properties":{
                "schema":"title,author,pages"
            }

          },
          {
            "uuid":"3333",
            "name":"PutHiveStreaming",
            "bundle":"cn.piflow.bundle.hive.PutHiveStreaming",
            "properties":{
                "database":"sparktest",
                "table":"dblp_phdthesis"
            }
          },
          {
            "uuid":"4444",
            "name":"CsvParser",
            "bundle":"cn.piflow.bundle.csv.CsvParser",
            "properties":{
                "csvPath":"hdfs://10.0.86.89:9000/xjzhu/phdthesis.csv",
                "header":"false",
                "delimiter":",",
                "schema":"title,author,pages"
            }
          },
          {
            "uuid":"555",
            "name":"Merge",
            "bundle":"cn.piflow.bundle.common.Merge",
            "properties":{
              "inports":"data1,data2"
            }
          },
          {
            "uuid":"666",
            "name":"Fork",
            "bundle":"cn.piflow.bundle.common.Fork",
            "properties":{
              "outports":"out1,out2,out3"
            }
          },
          {
            "uuid":"777",
            "name":"JsonSave",
            "bundle":"cn.piflow.bundle.json.JsonSave",
            "properties":{
              "jsonSavePath":"hdfs://10.0.86.89:9000/xjzhu/phdthesis.json"
            }
          },
          {
            "uuid":"888",
            "name":"CsvSave",
            "bundle":"cn.piflow.bundle.csv.CsvSave",
            "properties":{
              "csvSavePath":"hdfs://10.0.86.89:9000/xjzhu/phdthesis_result.csv",
              "header":"true",
              "delimiter":","
            }
          }
        ],
        "paths":[
          {
            "from":"XmlParser",
            "outport":"",
            "inport":"",
            "to":"SelectField"
          },
          {
            "from":"SelectField",
            "outport":"",
            "inport":"data1",
            "to":"Merge"
          },
          {
            "from":"CsvParser",
            "outport":"",
            "inport":"data2",
            "to":"Merge"
          },
          {
            "from":"Merge",
            "outport":"",
            "inport":"",
            "to":"Fork"
          },
          {
            "from":"Fork",
            "outport":"out1",
            "inport":"",
            "to":"PutHiveStreaming"
          },
          {
            "from":"Fork",
            "outport":"out2",
            "inport":"",
            "to":"JsonSave"
          },
          {
            "from":"Fork",
            "outport":"out3",
            "inport":"",
            "to":"CsvSave"
          }
        ]
      }
    }
  - curl -0 -X POST http://10.0.86.191:8002/flow/start -H "Content-type: application/json" -d 'this is your flow json'

## docker-started  
  - pull piflow images  
    docker pull registry.cn-hangzhou.aliyuncs.com/cnic_piflow/piflow:v0.6.1
    
  - show docker images  
    docker images
    
  - run a container with  piflow imageID ， all services run automatically  
    docker run --name piflow-v0.6 -it [imageID]
    
  - please visit "containerip:6001/piflow-web", it may take a while   
  
  - if somethings goes wrong,  all the application are in /opt  folder，
  
## use-interface
- `Login`:

  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-login.png)
  
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

- `Configure group`:

- `Monitor group`:

- `Process List`:

  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-processlist.png)
  
- `Template List`:

  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-templatelist.png)
  
- `Save Template`:

  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-savetemplate.png)
  
Welcome to join PiFlow User Group! Contact US  
Name:吴老师  
Mobile Phone：18910263390  
WeChat：18910263390  
Email: wzs@cnic.cn  
QQ Group：1003489545  
![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/PiFlowUserGroup_QQ.jpeg)



