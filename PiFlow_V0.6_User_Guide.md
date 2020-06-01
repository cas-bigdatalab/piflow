# 

# 1 引言

## 1.1 编写目的

该文档主要用于介绍大数据流水线系统piflow的使用

## 1.2 建设范围

Piflow server 及piflow web的使用说明

## 1.3 术语

l Piflow：大数据流水线系统

l Flow：大数据流水线；

l Stop：大数据流水线数据处理组件；

l Path: 每个大数据流水线数据处理组件之间的连接线；



# 2 项目概述

大数据流水线系统Piflow主要是针对大数据的ETL工具，它具有如下特性：

- 简单易用

- - 提供所见即所得页面配置流水线
  - 监控流水线状态
  - 查看流水线日志
  - 检查点功能

- 可扩展性

- - 支持用户自定义开发组件

- 性能优越

- - 基于分布式计算引擎Spark开发

- 功能强大

- - 提供100+数据处理组件
  - 包括 spark、mllib、hadoop、hive、hbase、solr、redis、memcache、elasticSearch、jdbc、mongodb、http、ftp、xml、csv、json等.



# 3 使用说明

## 3.1 界面说明

### 3.1.1 注册

![img](http://image-picgo.test.upcdn.net/img/20200530123823.jpg)

### 3.1.2 登录

![img](http://image-picgo.test.upcdn.net/img/20200530123825.jpg)

### 3.2.3 流水线列表

![img](http://image-picgo.test.upcdn.net/img/20200530123828.jpg)

  可点击进入流水线配置页面按钮，对流水线进行配置。

![img](http://image-picgo.test.upcdn.net/img/20200530123831.jpg)

可编辑流水线信息

![img](http://image-picgo.test.upcdn.net/img/20200530123835.jpg)

  可运行流水线

![img](http://image-picgo.test.upcdn.net/img/20200530123951.jpg)

  可删除流水线

![img](http://image-picgo.test.upcdn.net/img/20200530123954.jpg)

  可对流水线保存模板

![img](http://image-picgo.test.upcdn.net/img/20200530123957.jpg)

### 3.2.4 创建流水线

用户点击创建按钮，创建流水线。需要输入流水线名称及描述信息，同时可设置流水线需要的资源。

![img](http://image-picgo.test.upcdn.net/img/20200530124000.jpg)

### 3.4.5 配置流水线

用户可通过拖拽方式进行流水线的配置，方式类似visio，如下图所示。

![img](http://image-picgo.test.upcdn.net/img/20200530124003.jpg)

 

画布左边栏显示组件组和组件，可按关键字搜索。用户选择好组件后可拖至画布中央。

![img](http://image-picgo.test.upcdn.net/img/20200530124006.jpg)

画布右侧显示流水线基本信息，包括流水线名称及描述。

![img](http://image-picgo.test.upcdn.net/img/20200530124009.jpg)

画布中央选择任一数据处理组件，右侧显示该数据处理组件的基本信息，包括名称，描述，作者等信息。选择AttributeInfo tab，显示该数据处理组件的属性信息，用户可根据实际需求进行配置。

![img](http://image-picgo.test.upcdn.net/img/20200530124013.jpg)

 

### 3.4.6 运行流水线

用户配置好流水线后，可点击运行按钮运行流水线。

![img](http://image-picgo.test.upcdn.net/img/20200530124015.jpg)

### 3.4.7 流水线监控

加载完成之后，进入流水线监控页面。监控页面会显示整条流水线的执行状况，包括运行状态、执行进度、执行时间等。点击具体数据处理组件，显示该数据处理组件的运行状况，包括运行状态、执行时间。

![img](http://image-picgo.test.upcdn.net/img/20200530124018.jpg)

 

### 3.4.8 流水线日志

![img](http://image-picgo.test.upcdn.net/img/20200530124020.jpg)

 

### 3.4.9 运行流水线列表

  已运行流水线会显示在Process List中，包括开始时间、结束时间、进度、状态等。同时可对已运行流水线进行查看，在运行，停止，和删除操作。

![img](http://image-picgo.test.upcdn.net/img/20200530124023.jpg)

### 3.4.9 运行流水线检查点

![img](http://image-picgo.test.upcdn.net/img/20200530124026.jpg)

### 3.4.10 创建模板

  流水线可保存成模板

![img](http://image-picgo.test.upcdn.net/img/20200530124029.jpg)

![img](http://image-picgo.test.upcdn.net/img/20200530124032.jpg)

### 3.4.11 模板列表

保存的模板会显示在模板列表中。

![img](http://image-picgo.test.upcdn.net/img/20200530124034.jpg)

### 3.4.12 下载模板

  可下载模板，模板会保存成xml文件存放到本地。

![img](http://image-picgo.test.upcdn.net/img/20200530124037.jpg)

### 3.4.13 上传模板

![img](http://image-picgo.test.upcdn.net/img/20200530124040.jpg)

### 3.4.14 加载模板

![img](http://image-picgo.test.upcdn.net/img/20200530124043.jpg)

 

![img](http://image-picgo.test.upcdn.net/img/20200530124046.jpg)



 

## 3.2 Restful API



接口采用REST设计风格，目前需求如下接口：

### 3.2.1 getAllGroups



| **基本信息**   |                              |                                 |          |
| -------------- | ---------------------------- | ------------------------------- | -------- |
| 接口名称       | getAllGroups                 |                                 |          |
| 接口描述       | 获取所有数据处理组件Stop的组 |                                 |          |
| 接口URL        | GET /stop/ groups            |                                 |          |
| **参数说明**   |                              |                                 |          |
| 名称           | 描述                         | 类型                            | 数据类型 |
| 无             |                              |                                 |          |
| **返回值说明** |                              |                                 |          |
| 描述           | 类型                         | 实例                            |          |
| 返回所有组     | Json                         | {“groups”:”Common,Hive,Http,…”} |          |

 

### 3.2.2 getAllStops



| **基本信息**   |                      |                                            |          |
| -------------- | -------------------- | ------------------------------------------ | -------- |
| 接口名称       | getAllStops          |                                            |          |
| 接口描述       | 获取所有数据处理组件 |                                            |          |
| 接口URL        | GET /stop/list       |                                            |          |
| **参数说明**   |                      |                                            |          |
| 名称           | 描述                 | 类型                                       | 数据类型 |
| 无             |                      |                                            |          |
| **返回值说明** |                      |                                            |          |
| 描述           | 类型                 | 实例                                       |          |
| 返回所有Stop   | Json                 | {“stops”:”cn.piflow.bundle.Common.Fork,…”} |          |

 

### 3.2.3 getStopInfo



| **基本信息**     |                                |                                                              |          |
| ---------------- | ------------------------------ | ------------------------------------------------------------ | -------- |
| 接口名称         | getStopInfo                    |                                                              |          |
| 接口描述         | 获取数据处理组件Stop的详细信息 |                                                              |          |
| 接口URL          | GET /stop/info?bundle=***      |                                                              |          |
| **参数说明**     |                                |                                                              |          |
| 名称             | 描述                           | 类型                                                         | 数据类型 |
| bundle           | Stop的类名                     | Query                                                        | String   |
| **返回值说明**   |                                |                                                              |          |
| 描述             | 类型                           | 实例                                                         |          |
| 返回Stop详细信息 | Json                           | {"name":"LoadFromFtp","bundle":"cn.piflow.bundle.ftp.LoadFromFtp",“groups”:"ftp,load","description":"load  data from ftp  server","properties":[{"property":{"name":"url_str","displayName":"URL","description":null,"defaultValue":"","allowableValues":"","required":"true","sensitive":"false"}},{"property":{"name":"port","displayName":"PORT","description":null,"defaultValue":"","allowableValues":"","required":"true","sensitive":"false"}},{"property":{"name":"username","displayName":"USER_NAME","description":null,"defaultValue":"","allowableValues":"","required":"true","sensitive":"false"}},{"property":{"name":"password","displayName":"PASSWORD","description":null,"defaultValue":"","allowableValues":"","required":"true","sensitive":"false"}},{"property":{"name":"ftpFile","displayName":"FTP_File","description":null,"defaultValue":"","allowableValues":"","required":"true","sensitive":"false"}},{"property":{"name":"localPath","displayName":"Local_Path","description":null,"defaultValue":"","allowableValues":"","required":"true","sensitive":"false"}}]} |          |

### 3.2.4 startFlow



| **基本信息**         |                  |                                                              |
| -------------------- | ---------------- | ------------------------------------------------------------ |
| 接口名称             | startFlow        |                                                              |
| 接口描述             | 运行流水线       |                                                              |
| 接口URL              | POST /flow/start |                                                              |
| **参数说明**         |                  |                                                              |
| 描述                 | 类型             | 实例                                                         |
| Flow的json配置字符串 | String           | {"flow":{"name":"test","uuid":"1234","stops":[{"uuid":"1111","name":"XmlParser","bundle":"cn.piflow.bundle.xml.XmlParser","properties":{"xmlpath":"hdfs://10.0.86.89:9000/xjzhu/dblp.mini.xml","rowTag":"phdthesis"}},{"uuid":"2222","name":"SelectField","bundle":"cn.piflow.bundle.common.SelectField","properties":{"schema":"title,author,pages"}},{"uuid":"3333","name":"PutHiveStreaming","bundle":"cn.piflow.bundle.hive.PutHiveStreaming","properties":{"database":"sparktest","table":"dblp_phdthesis"}},{"uuid":"4444","name":"CsvParser","bundle":"cn.piflow.bundle.csv.CsvParser","properties":{"csvPath":"hdfs://10.0.86.89:9000/xjzhu/phdthesis.csv","header":"false","delimiter":",","schema":"title,author,pages"}},{"uuid":"555","name":"Merge","bundle":"cn.piflow.bundle.common.Merge","properties":{}},{"uuid":"666","name":"Fork","bundle":"cn.piflow.bundle.common.Fork","properties":{"outports":["out1","out2","out3"]}},{"uuid":"777","name":"JsonSave","bundle":"cn.piflow.bundle.json.JsonSave","properties":{"jsonSavePath":"hdfs://10.0.86.89:9000/xjzhu/phdthesis.json"}},{"uuid":"888","name":"CsvSave","bundle":"cn.piflow.bundle.csv.CsvSave","properties":{"csvSavePath":"hdfs://10.0.86.89:9000/xjzhu/phdthesis_result.csv","header":"true","delimiter":","}}],"paths":[{"from":"XmlParser","outport":"","inport":"","to":"SelectField"},{"from":"SelectField","outport":"","inport":"data1","to":"Merge"},{"from":"CsvParser","outport":"","inport":"data2","to":"Merge"},{"from":"Merge","outport":"","inport":"","to":"Fork"},{"from":"Fork","outport":"out1","inport":"","to":"PutHiveStreaming"},{"from":"Fork","outport":"out2","inport":"","to":"JsonSave"},{"from":"Fork","outport":"out3","inport":"","to":"CsvSave"}]} |
| **返回值说明**       |                  |                                                              |
| 描述                 | 类型             | 实例                                                         |
| 返回flow的appId      | String           | {“flow”:{“id”:”***”,”pid”:””***}}                            |

### 3.2.5 stopFlow



| **基本信息**   |                 |                 |
| -------------- | --------------- | --------------- |
| 接口名称       | stopFlow        |                 |
| 接口描述       | 停止流水线      |                 |
| 接口URL        | POST /flow/stop |                 |
| **参数说明**   |                 |                 |
| 描述           | 类型            | 实例            |
| Flow的appID    | String          | {“appID”:”***”} |
| **返回值说明** |                 |                 |
| 描述           | 类型            | 实例            |
| 返回执行状态   | String          | Ok/fail         |

 

### 3.2.6 getFlowInfo



| **基本信息**     |                          |                                                              |          |
| ---------------- | ------------------------ | ------------------------------------------------------------ | -------- |
| 接口名称         | getFlowInfo              |                                                              |          |
| 接口描述         | 获取流水线Flow的信息     |                                                              |          |
| 接口URL          | GET /flow/info?appID=*** |                                                              |          |
| **参数说明**     |                          |                                                              |          |
| 名称             | 描述                     | 类型                                                         | 数据类型 |
| appID            | Flow的Id                 | Query                                                        | String   |
| **返回值说明**   |                          |                                                              |          |
| 描述             | 类型                     | 实例                                                         |          |
| 返回Flow详细信息 | Json                     | {"flow":{"id":"application_1540442049798_0297","pid":"process_372bd7da-a53e-46b4-8c44-edc0463064f5_1","name":"xml,csv-merge-fork-hive,json,csv","state":"COMPLETED","startTime":"Tue  Nov 27 14:37:03 CST 2018","endTime":"Tue Nov 27 14:37:28  CST 2018","stops":[{"stop":{"name":"JsonSave","state":"COMPLETED","startTime":"Tue  Nov 27 14:37:24 CST 2018","endTime":"Tue Nov 27 14:37:28  CST 2018"}},{"stop":{"name":"CsvSave","state":"COMPLETED","startTime":"Tue  Nov 27 14:37:20 CST 2018","endTime":"Tue Nov 27 14:37:24  CST  2018"}},{"stop":{"name":"PutHiveStreaming","state":"COMPLETED","startTime":"Tue  Nov 27 14:37:13 CST 2018","endTime":"Tue Nov 27 14:37:20  CST 2018"}},{"stop":{"name":"Fork","state":"COMPLETED","startTime":"Tue  Nov 27 14:37:13 CST 2018","endTime":"Tue Nov 27 14:37:13  CST  2018"}},{"stop":{"name":"Merge","state":"COMPLETED","startTime":"Tue  Nov 27 14:37:11 CST 2018","endTime":"Tue Nov 27 14:37:11  CST 2018"}},{"stop":{"name":"SelectField","state":"COMPLETED","startTime":"Tue  Nov 27 14:37:11 CST 2018","endTime":"Tue Nov 27 14:37:11  CST  2018"}},{"stop":{"name":"XmlParser","state":"COMPLETED","startTime":"Tue  Nov 27 14:37:09 CST 2018","endTime":"Tue Nov 27 14:37:11  CST  2018"}},{"stop":{"name":"CsvParser","state":"COMPLETED","startTime":"Tue  Nov 27 14:37:03 CST 2018","endTime":"Tue Nov 27 14:37:09  CST 2018"}}]}} |          |

 

### 3.2.7 getFlowProgress



| **基本信息**   |                              |                                                              |          |
| -------------- | ---------------------------- | ------------------------------------------------------------ | -------- |
| 接口名称       | getFlowProgress              |                                                              |          |
| 接口描述       | 获取流水线Flow的执行进度     |                                                              |          |
| 接口URL        | GET /flow/progress?appID=*** |                                                              |          |
| **参数说明**   |                              |                                                              |          |
| 名称           | 描述                         | 类型                                                         | 数据类型 |
| appID          | Flow的Id                     | Query                                                        | String   |
| **返回值说明** |                              |                                                              |          |
| 描述           | 类型                         | 实例                                                         |          |
| 返回Flow的进度 | Json                         | {"flow":{"appId":"application_1540442049798_0297","name":"xml,csv-merge-fork-hive,json,csv","state":"COMPLETED","progress":"100%"}} |          |

 

### 3.2.8 getFlowLog



| **基本信息**   |                              |                                                              |          |
| -------------- | ---------------------------- | ------------------------------------------------------------ | -------- |
| 接口名称       | getFlowProgress              |                                                              |          |
| 接口描述       | 获取流水线Flow的执行进度     |                                                              |          |
| 接口URL        | GET /flow/progress?appID=*** |                                                              |          |
| **参数说明**   |                              |                                                              |          |
| 名称           | 描述                         | 类型                                                         | 数据类型 |
| appID          | Flow的Id                     | Query                                                        | String   |
| **返回值说明** |                              |                                                              |          |
| 描述           | 类型                         | 实例                                                         |          |
| 返回Flow的log  | Json                         | {"app":{"id":"application_1540442049798_0297","user":"root","name":"xml,csv-merge-fork-hive,json,csv","queue":"default","state":"FINISHED","finalStatus":"SUCCEEDED","progress":100.0,"trackingUI":"History","trackingUrl":"http://master:8088/proxy/application_1540442049798_0297/A","diagnostics":"","clusterId":1540442049798,"applicationType":"SPARK","applicationTags":"","startedTime":1543300611067,"finishedTime":1543300648590,"elapsedTime":37523,"amContainerLogs":"http://master:8042/node/containerlogs/container_1540442049798_0297_01_000001/root","amHostHttpAddress":"master:8042","allocatedMB":-1,"allocatedVCores":-1,"runningContainers":-1,"memorySeconds":217375,"vcoreSeconds":105,"preemptedResourceMB":0,"preemptedResourceVCores":0,"numNonAMContainerPreempted":0,"numAMContainerPreempted":0}} |          |

 

### 3.2.9 getFlowCheckPoints



| **基本信息**          |                                     |                              |          |
| --------------------- | ----------------------------------- | ---------------------------- | -------- |
| 接口名称              | getFlowCheckPoints                  |                              |          |
| 接口描述              | 获取流水线Flow的checkPoints         |                              |          |
| 接口URL               | GET /flow/checkpoints?processID=*** |                              |          |
| **参数说明**          |                                     |                              |          |
| 名称                  | 描述                                | 类型                         | 数据类型 |
| processID             | Flow的processID                     | Query                        | String   |
| **返回值说明**        |                                     |                              |          |
| 描述                  | 类型                                | 实例                         |          |
| 返回Flow的checkpoints | Json                                | {"checkpoints":"Merge,Fork"} |          |



 
