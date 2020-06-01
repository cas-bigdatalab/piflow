# PiFlowV0.7使用说明书

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

l Group：大数据流水线组

l Template：大数据流水线模板

l DataSource：数据源



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

![img](http://image-picgo.test.upcdn.net/img/20200530122455.jpg)

### 3.1.2 登录

![img](http://image-picgo.test.upcdn.net/img/20200530122458.jpg)

### 3.1.3 流水线Flow

#### 3.1.3.1 流水线列表

![img](http://image-picgo.test.upcdn.net/img/20200530122501.jpg)

 

Ø 可点击进入流水线配置页面按钮，对流水线进行配置。

![img](http://image-picgo.test.upcdn.net/img/20200530122506.jpg)

 

Ø 可编辑流水线信息

![img](http://image-picgo.test.upcdn.net/img/20200530122508.jpg)

 

Ø 可运行流水线

![img](http://image-picgo.test.upcdn.net/img/20200530122511.jpg)

 

Ø 可以debug模式运行流水线

![img](http://image-picgo.test.upcdn.net/img/20200530122515.jpg)

 

Ø 可删除流水线

![img](http://image-picgo.test.upcdn.net/img/20200530122519.jpg)

 

Ø 可对流水线保存模板

![img](http://image-picgo.test.upcdn.net/img/20200530122522.jpg)

#### 3.1.3.2 创建流水线

用户点击创建按钮，创建流水线。需要输入流水线名称及描述信息，同时可设置流水线需要的资源。

![img](http://image-picgo.test.upcdn.net/img/20200530122526.jpg)

#### 3.1.3.3 配置流水线

Ø 用户可通过拖拽方式进行流水线的配置，方式类似visio，如下图所示。

![img](http://image-picgo.test.upcdn.net/img/20200530122529.jpg)

 

Ø 画布左边栏显示组件组和组件，可按关键字搜索。用户选择好组件后可拖至画布中央。

![img](http://image-picgo.test.upcdn.net/img/20200530122533.jpg)

 

Ø 画布右侧显示流水线基本信息，包括流水线名称及描述。

![img](http://image-picgo.test.upcdn.net/img/20200530122536.jpg)

 

Ø 画布中央选择任一数据处理组件，右侧显示该数据处理组件的基本信息，包括名称，描述，作者等信息。选择AttributeInfo tab，显示该数据处理组件的属性信息，用户可根据实际需求进行配置。鼠标浮动到问号上会出现对应属性的说明，同时可以选择已设置好的数据源进行属性填充。

![img](http://image-picgo.test.upcdn.net/img/20200530122540.jpg)

 

![img](http://image-picgo.test.upcdn.net/img/20200530122543.jpg)

 

#### 3.1.3.4 运行流水线

Ø 用户配置好流水线后，可点击运行按钮运行流水线。

![img](http://image-picgo.test.upcdn.net/img/20200530122546.jpg)

#### 3.1.3.5 流水线监控

加载完成之后，进入流水线监控页面。监控页面会显示整条流水线的执行状况，包括运行状态、执行进度、执行时间等。点击具体数据处理组件，显示该数据处理组件的运行状况，包括运行状态、执行时间。

![img](http://image-picgo.test.upcdn.net/img/20200530122549.jpg)

![img](http://image-picgo.test.upcdn.net/img/20200530122552.jpg)

#### 3.1.3.6 流水线日志

![img](http://image-picgo.test.upcdn.net/img/20200530122555.jpg)

#### 3.1.3.7 调试流水线

Ø 可以以Debug模式运行流水线，运行后可查看流经每条线上的数据信息，实现数据可溯源

![img](http://image-picgo.test.upcdn.net/img/20200530122557.jpg)

 

![img](http://image-picgo.test.upcdn.net/img/20200530122600.jpg)

 

![img](http://image-picgo.test.upcdn.net/img/20200530122603.jpg)

#### 3.1.3.8 检查点

Ø 流水线可设置检查点，再次运行时可选择从检查点运行

![img](http://image-picgo.test.upcdn.net/img/20200530122606.jpg)

### 3.1.4 流水线组Group

#### 3.1.4.1 流水线组列表

Ø 流水线组支持流水线的调度功能，组嵌套功能。列表功能与流水线列表功能一致。

![img](http://image-picgo.test.upcdn.net/img/20200530122609.jpg)

#### 3.1.4.2 新建流水线组

Ø 点击创建按钮，输入流水线组名称和基本信息可创建流水线组Group。

![img](http://image-picgo.test.upcdn.net/img/20200530122612.jpg)

#### 3.1.4.3 配置流水线组

##### 3.2.4.3.1 创建group

Ø 拖动左侧group图标

![img](http://image-picgo.test.upcdn.net/img/20200530122615.jpg)

##### 3.2.4.3.2 创建flow

Ø 拖动flow图标创建流水线flow

![img](http://image-picgo.test.upcdn.net/img/20200530122618.jpg)

##### 3.2.4.3.3 创建label

Ø 拖动Label可添加标签，用于备注说明

![img](http://image-picgo.test.upcdn.net/img/20200530122622.jpg)

##### 3.2.4.3.4 创建调度关系

Ø 连线实现调度顺序

![img](http://image-picgo.test.upcdn.net/img/20200530122627.jpg)

##### 3.2.4.3.5 创建子group

Ø Group可双击进入，配置组内流水线组group、流水线flow、以及之间的调度顺序

![img](http://image-picgo.test.upcdn.net/img/20200530122630.jpg)

##### 3.2.4.3.6 配置流水线flow

Ø 双击flow图标，可进入具体流水线的配置界面

![img](http://image-picgo.test.upcdn.net/img/20200530122633.jpg)

##### 3.2.4.3.7 导入流水线flow

Ø 可导入flow列表中已配置的流水线

![img](http://image-picgo.test.upcdn.net/img/20200530122636.jpg)

 

##### 3.2.4.3.8 更换图标

Ø 右键group或flow，可支持更换图标

![img](http://image-picgo.test.upcdn.net/img/20200530122639.jpg)

 

Ø Group图标列表，支持用户上传

![image-20200530125104894](http://image-picgo.test.upcdn.net/img/20200530125105.png) 

Ø Flow图标列表，支持用户上传

![img](http://image-picgo.test.upcdn.net/img/20200530122641.jpg)

#### 3.1.4.4 运行流水线组

Ø 运行

![img](http://image-picgo.test.upcdn.net/img/20200530122644.jpg)

 

Ø 可右键运行单个group或flow

![img](http://image-picgo.test.upcdn.net/img/20200530122647.jpg)

 

![img](http://image-picgo.test.upcdn.net/img/20200530122649.jpg)

#### 3.1.4.5 监控流水线组

Ø 默认显示流水线组监控信息

![img](http://image-picgo.test.upcdn.net/img/20200530122653.jpg)

Ø 单击group或flow，显示点击组件的监控信息

![img](http://image-picgo.test.upcdn.net/img/20200530122655.jpg)

可双击进入group或flow，查看进一步监控信息

#### 3.1.4.6 流水线组日志

 

![img](http://image-picgo.test.upcdn.net/img/20200530122659.jpg)

### 3.1.5 运行态流水线Process

已运行流水线组和流水线会显示在Process List中，包括开始时间、结束时间、进度、状态等。同时可对已运行流水线进行查看，在运行，停止，和删除操作。

![img](http://image-picgo.test.upcdn.net/img/20200530122702.jpg)

### 3.1.6 模板Template

流水线组和流水线可保存成模板

#### 3.1.6.1 模板保存

Ø 流水线保存模板

![img](http://image-picgo.test.upcdn.net/img/20200530122705.jpg)

 

Ø 流水线组保存模板

![img](http://image-picgo.test.upcdn.net/img/20200530122708.jpg)

 

#### 3.1.6.2 模板列表

![img](http://image-picgo.test.upcdn.net/img/20200530122712.jpg)

 

#### 3.1.6.3 模板下载

![img](http://image-picgo.test.upcdn.net/img/20200530122715.jpg)

#### 3.1.6.4 模板上传

![img](http://image-picgo.test.upcdn.net/img/20200530122717.jpg)

 

#### 3.1.6.5 模板加载

Ø 流水线模板加载

![img](http://image-picgo.test.upcdn.net/img/20200530122721.jpg)

 

Ø 流水线组模板加载

![img](http://image-picgo.test.upcdn.net/img/20200530122724.jpg)

 

#### 3.1.6.6 模板删除

![img](http://image-picgo.test.upcdn.net/img/20200530122726.jpg)

 

 

![img](http://image-picgo.test.upcdn.net/img/20200530122731.jpg)



### 3.1.7 数据源

#### 3.1.7.1 创建数据源

Ø 支持JDBC、ElasticSearch、等数据源的创建。同时支持自定义数据源（other）

![img](http://image-picgo.test.upcdn.net/img/20200530122734.jpg)

#### 3.1.7.1 使用数据源

 

## 3.2 Restful API



接口采用REST设计风格，目前需求如下接口：

### 3.2.1 getAllGroups



| **基本信息**   |                                           |                                 |          |
| -------------- | ----------------------------------------- | ------------------------------- | -------- |
| 接口名称       | getAllGroups                              |                                 |          |
| 接口描述       | 获取所有数据处理组件Stop所在组            |                                 |          |
| 接口URL        | GET /stop/ groups                         |                                 |          |
| **参数说明**   |                                           |                                 |          |
| 名称           | 描述                                      | 类型                            | 数据类型 |
| 无             |                                           |                                 |          |
| **返回值说明** |                                           |                                 |          |
| 描述           | 返回代码                                  | 实例                            |          |
| 返回所有组信息 | 200                                       | {“groups”:”Common,Hive,Http,…”} |          |
| 500            | “getGroup Method Not Implemented  Error!” |                                 |          |

 

### 3.2.2 getAllStops



| **基本信息**   |                        |                                            |          |
| -------------- | ---------------------- | ------------------------------------------ | -------- |
| 接口名称       | getAllStops            |                                            |          |
| 接口描述       | 获取所有数据处理组件   |                                            |          |
| 接口URL        | GET /stop/list         |                                            |          |
| **参数说明**   |                        |                                            |          |
| 名称           | 描述                   | 类型                                       | 数据类型 |
| 无             |                        |                                            |          |
| **返回值说明** |                        |                                            |          |
| 描述           | 返回代码               | 实例                                       |          |
| 返回所有Stop   | 200                    | {“stops”:”cn.piflow.bundle.Common.Fork,…”} |          |
| 500            | “Can not found stop !” |                                            |          |

 

### 3.2.3 getStopInfo



| **基本信息**     |                                                              |                                                              |          |
| ---------------- | ------------------------------------------------------------ | ------------------------------------------------------------ | -------- |
| 接口名称         | getStopInfo                                                  |                                                              |          |
| 接口描述         | 获取数据处理组件Stop的详细信息                               |                                                              |          |
| 接口URL          | GET /stop/info?bundle=***                                    |                                                              |          |
| **参数说明**     |                                                              |                                                              |          |
| 名称             | 描述                                                         | 类型                                                         | 数据类型 |
| bundle           | Stop的类名                                                   | Query                                                        | String   |
| **返回值说明**   |                                                              |                                                              |          |
| 描述             | 返回代码                                                     | 实例                                                         |          |
| 返回Stop详细信息 | 200                                                          | {"name":"LoadFromFtp","bundle":"cn.piflow.bundle.ftp.LoadFromFtp",“groups”:"ftp,load","description":"load  data from ftp  server","properties":[{"property":{"name":"url_str","displayName":"URL","description":null,"defaultValue":"","allowableValues":"","required":"true","sensitive":"false"}},{"property":{"name":"port","displayName":"PORT","description":null,"defaultValue":"","allowableValues":"","required":"true","sensitive":"false"}},{"property":{"name":"username","displayName":"USER_NAME","description":null,"defaultValue":"","allowableValues":"","required":"true","sensitive":"false"}},{"property":{"name":"password","displayName":"PASSWORD","description":null,"defaultValue":"","allowableValues":"","required":"true","sensitive":"false"}},{"property":{"name":"ftpFile","displayName":"FTP_File","description":null,"defaultValue":"","allowableValues":"","required":"true","sensitive":"false"}},{"property":{"name":"localPath","displayName":"Local_Path","description":null,"defaultValue":"","allowableValues":"","required":"true","sensitive":"false"}}]} |          |
| 500              | “get PropertyDescriptor or getIcon Method Not  Implemented Error!” |                                                              |          |

### 3.2.4 startFlow



| **基本信息**         |                       |                                                              |
| -------------------- | --------------------- | ------------------------------------------------------------ |
| 接口名称             | startFlow             |                                                              |
| 接口描述             | 运行流水线            |                                                              |
| 接口URL              | POST /flow/start      |                                                              |
| **参数说明**         |                       |                                                              |
| 描述                 | 类型                  | 实例                                                         |
| Flow的json配置字符串 | String                | {"flow":{"name":"test","uuid":"1234","stops":[{"uuid":"1111","name":"XmlParser","bundle":"cn.piflow.bundle.xml.XmlParser","properties":{"xmlpath":"hdfs://10.0.86.89:9000/xjzhu/dblp.mini.xml","rowTag":"phdthesis"}},{"uuid":"2222","name":"SelectField","bundle":"cn.piflow.bundle.common.SelectField","properties":{"schema":"title,author,pages"}},{"uuid":"3333","name":"PutHiveStreaming","bundle":"cn.piflow.bundle.hive.PutHiveStreaming","properties":{"database":"sparktest","table":"dblp_phdthesis"}},{"uuid":"4444","name":"CsvParser","bundle":"cn.piflow.bundle.csv.CsvParser","properties":{"csvPath":"hdfs://10.0.86.89:9000/xjzhu/phdthesis.csv","header":"false","delimiter":",","schema":"title,author,pages"}},{"uuid":"555","name":"Merge","bundle":"cn.piflow.bundle.common.Merge","properties":{}},{"uuid":"666","name":"Fork","bundle":"cn.piflow.bundle.common.Fork","properties":{"outports":["out1","out2","out3"]}},{"uuid":"777","name":"JsonSave","bundle":"cn.piflow.bundle.json.JsonSave","properties":{"jsonSavePath":"hdfs://10.0.86.89:9000/xjzhu/phdthesis.json"}},{"uuid":"888","name":"CsvSave","bundle":"cn.piflow.bundle.csv.CsvSave","properties":{"csvSavePath":"hdfs://10.0.86.89:9000/xjzhu/phdthesis_result.csv","header":"true","delimiter":","}}],"paths":[{"from":"XmlParser","outport":"","inport":"","to":"SelectField"},{"from":"SelectField","outport":"","inport":"data1","to":"Merge"},{"from":"CsvParser","outport":"","inport":"data2","to":"Merge"},{"from":"Merge","outport":"","inport":"","to":"Fork"},{"from":"Fork","outport":"out1","inport":"","to":"PutHiveStreaming"},{"from":"Fork","outport":"out2","inport":"","to":"JsonSave"},{"from":"Fork","outport":"out3","inport":"","to":"CsvSave"}]} |
| **返回值说明**       |                       |                                                              |
| 描述                 | 返回代码              | 实例                                                         |
| 返回flow的appId      | 200                   | {“flow”:{“id”:”***”,”pid”:””***}}                            |
| 500                  | “Can not start flow!” |                                                              |

### 3.2.5 stopFlow



| **基本信息**   |                                |                 |
| -------------- | ------------------------------ | --------------- |
| 接口名称       | stopFlow                       |                 |
| 接口描述       | 停止流水线                     |                 |
| 接口URL        | POST /flow/stop                |                 |
| **参数说明**   |                                |                 |
| 描述           | 类型                           | 实例            |
| Flow的appID    | String                         | {“appID”:”***”} |
| **返回值说明** |                                |                 |
| 描述           | 返回代码                       | 实例            |
| 返回执行状态   | 200                            | “ok”            |
| 500            | “Can not found process Error!” |                 |

 

### 3.2.6 getFlowInfo



| **基本信息**     |                                     |                                                              |          |
| ---------------- | ----------------------------------- | ------------------------------------------------------------ | -------- |
| 接口名称         | getFlowInfo                         |                                                              |          |
| 接口描述         | 获取流水线Flow的信息                |                                                              |          |
| 接口URL          | GET /flow/info?appID=***            |                                                              |          |
| **参数说明**     |                                     |                                                              |          |
| 名称             | 描述                                | 类型                                                         | 数据类型 |
| appID            | Flow的Id                            | Query                                                        | String   |
| **返回值说明**   |                                     |                                                              |          |
| 描述             | 返回代码                            | 实例                                                         |          |
| 返回Flow详细信息 | 200                                 | {"flow":{"id":"application_1540442049798_0297","pid":"process_372bd7da-a53e-46b4-8c44-edc0463064f5_1","name":"xml,csv-merge-fork-hive,json,csv","state":"COMPLETED","startTime":"Tue  Nov 27 14:37:03 CST 2018","endTime":"Tue Nov 27 14:37:28  CST 2018","stops":[{"stop":{"name":"JsonSave","state":"COMPLETED","startTime":"Tue  Nov 27 14:37:24 CST 2018","endTime":"Tue Nov 27 14:37:28  CST 2018"}},{"stop":{"name":"CsvSave","state":"COMPLETED","startTime":"Tue  Nov 27 14:37:20 CST 2018","endTime":"Tue Nov 27 14:37:24  CST  2018"}},{"stop":{"name":"PutHiveStreaming","state":"COMPLETED","startTime":"Tue  Nov 27 14:37:13 CST 2018","endTime":"Tue Nov 27 14:37:20  CST 2018"}},{"stop":{"name":"Fork","state":"COMPLETED","startTime":"Tue  Nov 27 14:37:13 CST 2018","endTime":"Tue Nov 27 14:37:13  CST  2018"}},{"stop":{"name":"Merge","state":"COMPLETED","startTime":"Tue  Nov 27 14:37:11 CST 2018","endTime":"Tue Nov 27 14:37:11  CST 2018"}},{"stop":{"name":"SelectField","state":"COMPLETED","startTime":"Tue  Nov 27 14:37:11 CST 2018","endTime":"Tue Nov 27 14:37:11  CST  2018"}},{"stop":{"name":"XmlParser","state":"COMPLETED","startTime":"Tue  Nov 27 14:37:09 CST 2018","endTime":"Tue Nov 27 14:37:11  CST  2018"}},{"stop":{"name":"CsvParser","state":"COMPLETED","startTime":"Tue  Nov 27 14:37:03 CST 2018","endTime":"Tue Nov 27 14:37:09  CST 2018"}}]}} |          |
| 500              | “appID is null or flow run failed!” |                                                              |          |

 

### 3.2.7 getFlowProgress



| **基本信息**   |                                     |                                                              |          |
| -------------- | ----------------------------------- | ------------------------------------------------------------ | -------- |
| 接口名称       | getFlowProgress                     |                                                              |          |
| 接口描述       | 获取流水线Flow的执行进度            |                                                              |          |
| 接口URL        | GET /flow/progress?appID=***        |                                                              |          |
| **参数说明**   |                                     |                                                              |          |
| 名称           | 描述                                | 类型                                                         | 数据类型 |
| appID          | Flow的Id                            | Query                                                        | String   |
| **返回值说明** |                                     |                                                              |          |
| 描述           | 返回代码                            | 实例                                                         |          |
| 返回Flow的进度 | 200                                 | {"flow":{"appId":"application_1540442049798_0297","name":"xml,csv-merge-fork-hive,json,csv","state":"COMPLETED","progress":"100%"}} |          |
| 500            | “appId is null or flow run failed!” |                                                              |          |

 

### 3.2.8 getFlowLog



| **基本信息**        |                                         |                                                              |          |
| ------------------- | --------------------------------------- | ------------------------------------------------------------ | -------- |
| 接口名称            | getFlowProgress                         |                                                              |          |
| 接口描述            | 获取流水线Flow的执行进度                |                                                              |          |
| 接口URL             | GET /flow/log?appID=***                 |                                                              |          |
| **参数说明**        |                                         |                                                              |          |
| 名称                | 描述                                    | 类型                                                         | 数据类型 |
| appID               | Flow的Id                                | Query                                                        | String   |
| **返回值说明**      |                                         |                                                              |          |
| 描述                | 返回代码                                | 实例                                                         |          |
| 返回Flow的log的地址 | 200                                     | {"app":{"id":"application_1540442049798_0297","user":"root","name":"xml,csv-merge-fork-hive,json,csv","queue":"default","state":"FINISHED","finalStatus":"SUCCEEDED","progress":100.0,"trackingUI":"History","trackingUrl":"http://master:8088/proxy/application_1540442049798_0297/A","diagnostics":"","clusterId":1540442049798,"applicationType":"SPARK","applicationTags":"","startedTime":1543300611067,"finishedTime":1543300648590,"elapsedTime":37523,"amContainerLogs":"http://master:8042/node/containerlogs/container_1540442049798_0297_01_000001/root","amHostHttpAddress":"master:8042","allocatedMB":-1,"allocatedVCores":-1,"runningContainers":-1,"memorySeconds":217375,"vcoreSeconds":105,"preemptedResourceMB":0,"preemptedResourceVCores":0,"numNonAMContainerPreempted":0,"numAMContainerPreempted":0}} |          |
| 500                 | “appID is null or flow does not exist!” |                                                              |          |

 

### 3.2.9 getFlowCheckPoints



| **基本信息**          |                                         |                              |          |
| --------------------- | --------------------------------------- | ---------------------------- | -------- |
| 接口名称              | getFlowCheckPoints                      |                              |          |
| 接口描述              | 获取流水线Flow的checkPoints             |                              |          |
| 接口URL               | GET /flow/checkpoints?appID=***         |                              |          |
| **参数说明**          |                                         |                              |          |
| 名称                  | 描述                                    | 类型                         | 数据类型 |
| appID                 | Flow的appID                             | Query                        | String   |
| **返回值说明**        |                                         |                              |          |
| 描述                  | 返回代码                                | 实例                         |          |
| 返回Flow的checkpoints | 200                                     | {"checkpoints":"Merge,Fork"} |          |
| 500                   | “appID is null or flow does not exist!” |                              |          |



### 3.2.10 getFlowDebugData

| **基本信息**                                 |                                          |                                     |          |
| -------------------------------------------- | ---------------------------------------- | ----------------------------------- | -------- |
| 接口名称                                     | getFlowDebugData                         |                                     |          |
| 接口描述                                     | 获取流水线Flow的调试数据                 |                                     |          |
| 接口URL                                      | GET /flow/debugData?appID=***            |                                     |          |
| **参数说明**                                 |                                          |                                     |          |
| 名称                                         | 描述                                     | 类型                                | 数据类型 |
| appID                                        | Flow的appID                              | Query                               | String   |
| stopName                                     | stop的名称                               | Query                               | String   |
| Port                                         | Stop的端口名                             | Query                               | String   |
| **返回值说明**                               |                                          |                                     |          |
| 描述                                         | 返回代码                                 | 实例                                |          |
| 返回Flow的指定stop和端口的调试数据的hdfs路径 | 200                                      | {"schema":””,  “debugDataPath”:" "} |          |
| 500                                          | “appID  is null or flow does not exist!” |                                     |          |

### 3.2.11 startFlowGroup

| **基本信息**              |                   |                                                              |
| ------------------------- | ----------------- | ------------------------------------------------------------ |
| 接口名称                  | startFlowGroup    |                                                              |
| 接口描述                  | 运行流水线组      |                                                              |
| 接口URL                   | POST /group/start |                                                              |
| **参数说明**              |                   |                                                              |
| 描述                      | 类型              | 实例                                                         |
| FlowGroup的json配置字符串 | String            | {"group":{"flows":[{"flow":{"executorNumber":"1","driverMemory":"1g","executorMemory":"1g","executorCores":"1","paths":[{"inport":"","from":"MockData","to":"ShowData","outport":""}],"name":"f4","stops":[{"customizedProperties":{},"name":"MockData","uuid":"8a80d63f720cdd2301723b7745b72649","bundle":"cn.piflow.bundle.common.MockData","properties":{"schema":"title:String,author:String,age:Int","count":"10"}},{"customizedProperties":{},"name":"ShowData","uuid":"8a80d63f720cdd2301723b7745b72647","bundle":"cn.piflow.bundle.external.ShowData","properties":{"showNumber":"5"}}],"uuid":"8a80d63f720cdd2301723b7745b62645"}},{"flow":{"executorNumber":"1","driverMemory":"1g","executorMemory":"1g","executorCores":"1","paths":[{"inport":"","from":"MockData","to":"ShowData","outport":""}],"name":"f3","stops":[{"customizedProperties":{},"name":"MockData","uuid":"8a80d63f720cdd2301723b7745b9265d","bundle":"cn.piflow.bundle.common.MockData","properties":{"schema":"title:String,author:String,age:Int","count":"10"}},{"customizedProperties":{},"name":"ShowData","uuid":"8a80d63f720cdd2301723b7745b9265b","bundle":"cn.piflow.bundle.external.ShowData","properties":{"showNumber":"5"}}],"uuid":"8a80d63f720cdd2301723b7745b82659"}}],"name":"SimpleGroup","groups":[{"group":{"flows":[{"flow":{"executorNumber":"1","driverMemory":"1g","executorMemory":"1g","executorCores":"1","paths":[{"inport":"","from":"MockData","to":"ShowData","outport":""}],"name":"MockData","stops":[{"customizedProperties":{},"name":"MockData","uuid":"8a80d63f720cdd2301723b7745b4261a","bundle":"cn.piflow.bundle.common.MockData","properties":{"schema":"title:String,author:String,age:Int","count":"10"}},{"customizedProperties":{},"name":"ShowData","uuid":"8a80d63f720cdd2301723b7745b32618","bundle":"cn.piflow.bundle.external.ShowData","properties":{"showNumber":"5"}}],"uuid":"8a80d63f720cdd2301723b7745b32616"}},{"flow":{"executorNumber":"1","driverMemory":"1g","executorMemory":"1g","executorCores":"1","paths":[{"inport":"","from":"MockData","to":"ShowData","outport":""}],"name":"MockData","stops":[{"customizedProperties":{},"name":"MockData","uuid":"8a80d63f720cdd2301723b7745b5262e","bundle":"cn.piflow.bundle.common.MockData","properties":{"schema":"title:String,author:String,age:Int","count":"10"}},{"customizedProperties":{},"name":"ShowData","uuid":"8a80d63f720cdd2301723b7745b5262c","bundle":"cn.piflow.bundle.external.ShowData","properties":{"showNumber":"5"}}],"uuid":"8a80d63f720cdd2301723b7745b4262a"}}],"name":"g1","uuid":"8a80d63f720cdd2301723b7745b22615"}}],"conditions":[{"entry":"f4","after":"g1"},{"entry":"f3","after":"g1"}],"uuid":"8a80d63f720cdd2301723b7745b22614"}} |
| **返回值说明**            |                   |                                                              |
| 描述                      | 返回代码          | 实例                                                         |
| 返回flowGroup的Id         | 200               | {"group":{"id":"group_fc1cb223-9c44-467f-a063-e959ffb6bcd8"}} |
|                           | 500               | “Can not  start group!”                                      |

 

### 3.2.12 stopFlowGroup

| **基本信息**              |                  |                                   |
| ------------------------- | ---------------- | --------------------------------- |
| 接口名称                  | stopFlowGroup    |                                   |
| 接口描述                  | 停止流水线组     |                                   |
| 接口URL                   | POST /group/stop |                                   |
| **参数说明**              |                  |                                   |
| 描述                      | 类型             | 实例                              |
| FlowGroup的json配置字符串 | String           | {“groupId”:”***”}                 |
| **返回值说明**            |                  |                                   |
| 描述                      | 返回代码         | 实例                              |
| 返回停止操作的状态        | 200              | “Stop  FlowGroup OK!!!”           |
|                           | 500              | “Can not  found FlowGroup Error!” |

 

### 3.2.13 getFlowGroupInfo

| **基本信息**   |                                   |                                                              |
| -------------- | --------------------------------- | ------------------------------------------------------------ |
| 接口名称       | getFlowGroupInfo                  |                                                              |
| 接口描述       | 获取流水线组信息                  |                                                              |
| 接口URL        | GET /group/info?groupID=***       |                                                              |
| **参数说明**   |                                   |                                                              |
| 名称           | 描述                              | 类型                                                         |
| groupId        | GroupId                           | String                                                       |
| **返回值说明** |                                   |                                                              |
| 描述           | 返回代码                          | 实例                                                         |
| 返回group信息  | 200                               | {"group":{"name":"SimpleGroup","startTime":"FriMay2918:10:50CST2020","state":"STARTED","flows":[],"groups":[{"group":{"name":"g1","startTime":"FriMay2918:10:50CST2020","state":"COMPLETED","flows":[{"flow":{"name":"MockData","startTime":"FriMay2918:11:03CST2020","state":"COMPLETED","endTime":"FriMay2918:11:07CST2020","id":"application_1589249052248_0440","pid":"process_b3c96bf0-c9b4-41b1-b0e0-06fb2d5e4be5_1","progress":"100","stops":[{"stop":{"name":"ShowData","state":"COMPLETED","startTime":"FriMay2918:11:07CST2020","endTime":"FriMay2918:11:07CST2020"}},{"stop":{"name":"MockData","state":"COMPLETED","startTime":"FriMay2918:11:03CST2020","endTime":"FriMay2918:11:07CST2020"}}]}}],"groups":[],"endTime":"FriMay2918:11:20CST2020","id":"group_2322a41d-7b69-4fe7-9a87-a78c50f26e09"}}],"endTime":"","id":"group_0a7abbd3-9c9a-4dfa-9a0b-7f77fdacf3d4"}} |
| 500            | “Can not  found FlowGroup Error!” |                                                              |

 

### 3.2.14 getFlowGroupProgress

| **基本信息**   |                                                     |        |
| -------------- | --------------------------------------------------- | ------ |
| 接口名称       | getFlowGroupProgress                                |        |
| 接口描述       | 获取流水线group的执行进度                           |        |
| 接口URL        | GET /group/progress?groupId=***                     |        |
| **参数说明**   |                                                     |        |
| 名称           | 描述                                                | 类型   |
| groupId        | Group的id                                           | String |
| **返回值说明** |                                                     |        |
| 描述           | 返回代码                                            | 实例   |
| 返回执行进度   | 200                                                 | “100”  |
| 500            | “groupId  is null or flowGroup progress exception!” |        |

 
