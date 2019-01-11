![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow.png) 
is an easy to use, powerful big data pipeline system.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Requirements](#requirements)
- [Getting Started](#getting-started)
- [Getting Help](#getting-help)
- [Documentation](#documentation)

## Features

- Easy to use
  - provide a WYSIWYG web interface to configure data flow
  - monitor big data flow status
  - check big data flow logs
  - provide checkpoint
- Strong Scalability:
  - Support for custom development data processing components
- Superior performance
  - based on distributed computing engine Spark 
- Powerful
  - 100+ data processing components available
  - include spark、mllib、hadoop、hive、hbase、solr、redis、memcache、elasticSearch、jdbc、mongodb、http、ftp、xml、csv、json，etc.

## Architecture
![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/architecture.png) 
## Requirements
* JDK 1.8 or newer
* Apache Maven 3.1.0 or newer
* Git Client (used during build process by 'bower' plugin)
* spark-2.1.0
* hadoop-2.6.0

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
- configure config.properties

      #server ip and port
      server.ip=10.0.86.191
      server.port=8002
      h2.port=50002
      
      #spark and yarn config
      spark.master=yarn
      spark.deploy.mode=cluster
      yarn.resourcemanager.hostname=10.0.86.191
      yarn.resourcemanager.address=10.0.86.191:8032
      yarn.access.namenode=hdfs://10.0.86.191:9000
      yarn.stagingDir=hdfs://10.0.86.191:9000/tmp/
      yarn.jars=hdfs://10.0.86.191:9000/user/spark/share/lib/*.jar
      yarn.url=http://10.0.86.191:8088/ws/v1/cluster/apps/

      #hive config
      hive.metastore.uris=thrift://10.0.86.191:9083

      #piflow jar path
      piflow.bundle=/opt/piflowServer/piflow-server-0.9.jar

      #checkpoint hdfs path
      checkpoint.path=hdfs://10.0.86.89:9000/piflow/checkpoints/
- you can run piflow server on intellij 
  - main class is cn.piflow.api.Main
  - remember to set SPARK_HOME
- you can run piflow server as follows:
  - download piflowServer:***
  - edit config.properties
  - run start.sh
  
To Run Piflow Web：
  - todo
  
To Use：

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
- piflow web
  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow_web.png)
