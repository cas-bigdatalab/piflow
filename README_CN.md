![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-logo2.png) 
PiFlow是一个简单易用，功能强大的大数据流水线系统。

## 目录

- [特性](#特性)
- [架构](#架构)
- [要求](#要求)
- [开始](#开始)

## 特性

- 简单易用
  - 可视化配置流水线
  - 监控流水线
  - 查看流水线日志
  - 检查点功能
  
- 扩展性强:
  - 支持自定义开发数据处理组件
  
- 性能优越：
  - 基于分布式计算引擎Spark开发 
  
- 功能强大：
  - 提供100+的数据处理组件
  - 包括Hadoop 、Spark、MLlib、Hive、Solr、Redis、MemCache、ElasticSearch、JDBC、MongoDB、HTTP、FTP、XML、CSV、JSON等
  - 集成了微生物领域的相关算法

## 架构
![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/architecture.png) 
## 要求
* JDK 1.8 及以上版本
* Apache Maven 3.1.0 及以上版本
* Git Client 
* Spark-2.1.0 及以上版本
* Hadoop-2.6.0 及以上版本

## 开始

如何Build: 
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

如何运行Piflow Server：

- `使用Intellij Idea`: 
  - 编辑config.properties文件
  - build piflow工程，生成piflow-server.jar
  - 运行cn.piflow.api.Main
  - 切记设置SPARK_HOME
  
- `直接运行release版本`:
  - 下载release版本，地址：https://github.com/cas-bigdatalab/piflow_release
  - 将build好的piflow-server.jar拷贝到piflow_release文件夹（由于git不能上传超过1G大文件，故需自行build piflow-server.jar）
  - 编辑config.properties文件
  - 运行start.sh 或者后台运行 nohup ./start.sh > piflow.log 2>&1 &
- `如何配置config.properties`

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

      #piflow-server.jar path
      piflow.bundle=/opt/piflowServer/piflow-server-0.9.jar

      #checkpoint hdfs path
      checkpoint.path=hdfs://10.0.86.89:9000/piflow/checkpoints/
      
      #debug path
      debug.path=hdfs://10.0.88.191:9000/piflow/debug/
      
      #yarn url
      yarn.url=http://10.0.86.191:8088/ws/v1/cluster/apps/
      
      #the count of data shown in log
      data.show=10
      
      #h2 db port
      h2.port=50002
  
如何运行Piflow Web：
  - https://github.com/cas-bigdatalab/piflow-web
  
如何使用：

- 命令行方式
  - 流水线样例配置
  

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
  - 运行命令
    - curl -0 -X POST http://serverIP:serverPort/flow/start -H "Content-type: application/json" -d '你的流水线json配置文件'
- 访问piflow web: 试运行地址 "http://piflow.ml/piflow-web", user/password: admin/admin
  - 登录
  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-login.png)
  - 流水线列表
  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-flowlist.png)
  - 流水线配置
  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-congfigflow.png)
  - 流水线资源配置
  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-resource.png)
  - 运行流水线
  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-run.png)
  - 删除流水线
  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-delete.png)
  - 流水线保存模板
  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-savetemplate.png)
  - 创建流水线:用户点击创建按钮,需要输入流水线名称及描述信息,同时可设置流水线需要的资源.
  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-createflows.png)
  - 配置流水线:用户可通过拖拽方式进行流水线的配置，方式类似visio
  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-flowconfig.png)
  - 搜索流水线组件：画布左边栏显示组件组和组件，可按关键字搜索,户选择好组件后可拖至画布中央
  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-module.png)
  - 流水线基本信息：画布右侧显示流水线基本信息，包括流水线名称及描述
  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-message.png)
  - 流水线配置：画布中央选择任一数据处理组件,右侧显示该数据处理组件的基本信息,包括名称描述,作者等信息.选择AttributeInfo tab,显示该数据处理组件的属性信息,用户可根据实际需求进行配置
  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-randomconfig.png)
  - 运行流水线：用户配置好流水线后,可点击运行按钮运行流水线
  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-runpiflow.png)
  - 流水线监控：进入流水线监控页面。监控页面会显示整条流水线的执行状况，包括运行状态、执行进度、执行时间等,击具体数据处理组件，显示该数据处理组件的运行状况，包括运行状态、执行时间。
  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-control.png)
  - 查看流水线日志
  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-log.png)
  - 运行中流水线列表: 已运行流水线会显示在Process List中，包括开始时间、结束时间、进度、状态等。同时可对已运行流水线进行查看，在运行，停止，和删除操作
  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-processlist.png)
  - 运行流水线检查点
  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-runcheckpoint.png)
  - 创建保存模板
  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-savetemplates.png)
  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-savetemplatess.png)
  - 模板列表
  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-templatelist.png)
  - 下载模板：模板会保存成xml文件存放到本地
  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-download.png)
  - 上传模板
  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-upload.png)
  - 加载模板
  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-load1.png)
  ![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/piflow-load2.png)
  
