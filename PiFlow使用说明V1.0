## 编写目的

该文档主要用于介绍大数据流水线系统PiFlow 的使用

## 建设范围

PiFlow server 及PiFlow web的使用说明

## 术语

-   PiFlow ：大数据流水线系统；

-   Flow：大数据流水线；

-   Stop：大数据流水线数据处理组件；

-   Path: 每个大数据流水线数据处理组件之间的连接线；

-   Group：大数据流水线组，支持流水线/流水线组的顺序调度；

-   Template：大数据流水线模板，支持将流水线/流水线组保存成模板、下载、上传和加载；

-   DataSource：数据源，支持FTP、JDBC、ElasticSearch、Hive等数据源注册，支持自定义数据源；

-   Schedule：大数据流水线调度，支持流水线/流水线组的调度及定时调度

-   StopsHub：组件热插拔，支持用户开发自定义组件一键上传

-   SparkJar: spark jar依赖包管理

# 项目概述

大数据流水线系统PiFlow 主要是针对大数据的ETL工具，它具有如下特性：

-   简单易用

    -   提供所见即所得页面配置流水线

    -   监控流水线状态

    -   查看流水线日志

    -   检查点功能

    -   调度功能

    -   组件热插拔功能

-   可扩展性

    -   支持用户自定义开发组件

-   性能优越

    -   基于分布式计算引擎Spark开发

-   功能强大

    -   提供100+数据处理组件

    -   包括
        spark、mllib、hadoop、hive、hbase、solr、redis、memcache、elasticSearch、jdbc、mongodb、http、ftp、xml、csv、json等.

# 使用说明

## 3.1 界面说明

### 3.1.1 注册

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/804bb965d44bc42d78980ab035863bf6.png)

### 3.1.2 登录

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/0fb8f864b8b8771cb4b112f01b99a1b4.png)

### 3.1.4 首页

首页展示了资源使用情况，包括CPU、内存和磁盘。同时，展示了流水线Flow的总体情况、Group的总体情况、调度Schedule的总体情况、数据源DataSource的总体情况、数据处理组件的基本情况。其中Processor为运行态流水线/流水线组，状态可分为Started开始、完成Completed、失败Failed、Killed杀死、其他Other状态。

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/2ba4f0258d7c1ce88b5d9a62951d69ec.png)

同时，支持了国际化，如下图所示。

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/37c5fd88e21160456829b81ef0da6e17.png)

### 3.1.4 流水线Flow

#### 3.1.4.1 流水线列表

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/ce3c14c203f683dbb6352bc65bd485c3.png)

-   可点击进入流水线配置页面按钮，对流水线进行配置。

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/3370e78c6400dd8da9a74c6aad38e26c.png)

-   可编辑流水线信息

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/314bdac455964e5c9147aa60f196e38c.png)

-   可运行流水线

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/c8026939816d22732be62f3ee74a69d2.png)

-   可以debug模式运行流水线

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/98188fa9ff6e34c5ed847a9b8a6a8f06.png)

-   可删除流水线

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/e0fe4e3ce81df3a2c6bcbf9011665d0b.png)

-   可对流水线保存模板

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/4b55ce202cb56a84b9f3c379f52457d4.png)

#### 3.1.4.2 创建流水线

用户点击创建按钮，创建流水线。需要输入流水线名称及描述信息，同时可设置流水线需要的资源。

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/3773464b6a0681231693e93907a14913.png)

#### 3.1.4.3 配置流水线

-   用户可通过拖拽方式进行流水线的配置，方式类似visio，如下图所示。

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/196a7a99a6675b13de7b16280a771ed1.png)

-   画布左边栏显示组件组和组件，可按关键字搜索。用户选择好组件后可拖至画布中央。

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/5e41f29adc56f48a11e366cb71964b1e.png)

-   画布右侧显示流水线基本信息，包括流水线名称及描述。

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/9a8d4dcf9ec91763d84da112503b8746.png)

-   画布中央选择任一数据处理组件，右侧显示该数据处理组件的基本信息，包括名称，描述，作者等信息。选择AttributeInfo
    Tab，显示该数据处理组件的属性信息，用户可根据实际需求进行配置。鼠标浮动到问号上会出现对应属性的说明，同时可以选择已设置好的数据源进行属性填充。

    数据处理组件基本信息如下图所示，点击StopName可对数据处理组件进行改名。

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/224b0701fe371ea188c486a965479af7.png)

数据处理组件属性信息设置如下图所示。“问号”按钮提示该属性描述信息，“红星”表示必填项。

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/ac4a2020b57ad8a89baf3a5baff79041.png)

数据处理组件属性样例信息如下图所示：

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/fb46f7d107154685d461da70d58fee95.png)

数据处理组件数据源填充如下图所示。已选择数据源相关数据会自动填充到所选数据处理组件中。数据源变更后，相应组件的属性也会随之更新。

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/c9aca3f7fdf518b303dfd89eb531583e.png)

#### 3.1.4.4 运行流水线

用户配置好流水线后，可点击运行按钮运行流水线。

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/298f03ec66e58bbffa4b39bfde561a73.png)

支持运行单个数据处理组件和当前及以下数据处理组件。

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/ca448a8e10ab5c9d6f3d7784186ef450.png)

针对选中数据处理组件，需要给端口指定数据来源（测试数据管理，详见3.1.12）后运行

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/c6ba04b0642ecba881e6781052bca0ce.png)

#### 3.1.4.5 流水线监控

加载完成之后，进入流水线监控页面。监控页面会显示整条流水线的执行状况，包括运行状态、执行进度、执行时间等。

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/4b7aa225d667724cf4d131203ef4b38a.png)

点击具体数据处理组件，显示该数据处理组件的运行状况，包括运行状态、执行时间。

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/94819e5c8445407656ab2a448f056d89.png)

#### 3.1.4.6 流水线日志

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/f19aec5e6da383e3f4fd82deeaa2d73d.png)

#### 3.1.4.7 调试流水线

-   可以以Debug模式运行流水线，运行后可查看流经每条线上的数据信息，实现数据可溯源

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/bea241c3479deca8085bd1480ca46c7d.png)

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/458067709215b1f7a74448ada1c562da.png)

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/3fb3c84ac73286d9f9292cf635a8ef78.png)

#### 3.1.4.8 检查点

-   流水线可设置检查点，再次运行时可选择从检查点运行

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/d8fef3b9b572baf509ef6c005f6377ad.png)

#### 3.1.4.9 可视化组件

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/938789ca2232d5a79f7c0b6ed5aa349c.png)

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/20ab6f45ca3a76fe1fe1e854eae1e6a3.png)

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/02c5f7d5142128486bec25629ad12298.png)

#### 3.1.4.10 表格组件

TableShow组件可以按表格形式展示数据。

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/97b1b2e80e9d2d451c87de60f8c7d221.png)

数据可以直接导出

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/7b1ff06a83237e146cb5a578c2d64f82.png)

### 3.1.5 流水线组Group

#### 3.1.5.1 流水线组列表

-   流水线组支持流水线的顺序调度功能，组嵌套功能。列表功能与流水线列表功能一致。列表支持进入、编辑、运行/停止、删除、保存模板功能。

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/3e2b75a920dab6e8e80223ea55e4138c.png)

#### 3.1.5.2 新建流水线组

-   点击创建按钮，输入流水线组名称和基本信息可创建流水线组Group。

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/2098c1b0bc900e3ef6784f190b90ea03.png)

#### 3.1.5.3 配置流水线组

##### 3.1.5.3.1 创建group

-   拖动左侧group图标

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/962d857fa6d81841b68e7d66fec1fab7.png)

##### 3.1.5.3.2 创建flow

-   拖动flow图标创建流水线flow

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/0ce7214d28dfafa361eb71797b420208.png)

##### 3.1.5.3.3 创建label

-   拖动Label可添加标签，用于备注说明

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/691a0860ccc3550de400e40fff27d9aa.png)

##### 3.1.5.3.4 创建调度关系

-   连线实现调度顺序

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/5d252f945b58e243b67e17db0bdd3266.png)

##### 3.1.5.3.5 创建子group

-   Group可双击进入，配置组内流水线组group、流水线flow、以及之间的调度顺序。下部有导航栏，可退出该级目录，返回上一级。同时可以返回根目录。

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/c37366a416edcbdbc8d3e156b2c17728.png)

##### 3.1.5.3.6 配置流水线flow

-   双击flow图标，可进入具体流水线的配置界面

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/74004a9c950b9938546b9bc4d60d1a6d.png)

##### 3.1.5.3.7 导入流水线flow

-   可导入flow列表中已配置的流水线

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/e40afa0d5300a994c13fb71d60edb02d.png)

##### 3.1.5.3.8 更换图标

-   右键group或flow，可支持更换图标

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/723edc23349f5db4e0206ab84f9183f3.png)

-   Group图标列表，支持用户上传

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/778fc60b703609d7bed36c1d3ddf1b65.png)

-   Flow图标列表，支持用户上传

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/9a586cd3d63b62ebe0468a556cbb48c8.png)

#### 3.1.5.4 运行流水线组

-   运行

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/ba6ace4a165ebe4103022d51d925a809.png)

-   可右键运行单个group或flow

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/6fcd81e765e4b35e6856d7e256a52c93.png)

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/2cc6a0aa5fae6bf352e05b520f688a79.png)

#### 3.1.5.5 监控流水线组

-   默认显示流水线组监控信息

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/eac334b51f911c2ab6485637ec3a61a8.png)

-   单击group或flow，显示点击组件的监控信息

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/5d46f397da6d8fe00d59881e51e0489f.png)

可双击进入group或flow，查看进一步监控信息

#### 3.1.5.6 流水线组日志

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/fd427e60a1bf0cf972af6def8de99d62.png)

### 3.1.6 运行态流水线Process

已运行流水线组和流水线会显示在Process
List中，包括开始时间、结束时间、进度、状态等。同时可对已运行流水线进行查看，在运行，停止，和删除操作。

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/d08ecc7d6809d724e193abb87bee4579.png)

### 3.1.7 模板Template

流水线组和流水线可保存成模板

#### 3.1.7.1 模板保存

-   流水线保存模板

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/843ef0e7d2ef3d8ae9b25fb7643e124a.png)

-   流水线组保存模板

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/222be5da30a64ff4a5f0ea6a775fda84.png)

#### 3.1.7.2 模板列表

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/551a4be7c3ed491e61b33ca06fc95a75.png)

#### 3.1.7.3 模板下载

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/5a303edbe77897f3affcaf8b92ed66cb.png)

#### 3.1.7.4 模板上传

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/3f7d71f9be11017717a6657f2acb378c.png)

#### 3.1.7.5 模板加载

-   流水线模板加载

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/69f40f0793cf7ac591a41a693811d7b3.png)

-   流水线组模板加载

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/22734e828f3636d889c561d2779fe09a.png)

#### 3.1.7.6 模板删除

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/5974d3c28593d699e9c5e05326273b0b.png)

### 3.1.8 数据源

#### 3.1.8.1 创建数据源

-   支持JDBC、ElasticSearch、等数据源的创建。同时支持自定义数据源（other）

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/697b4d7a34548ae8cc38d2ea2b678830.png)

#### 3.1.8.1 使用数据源

在流水线配置页面，选择某个组件，设置该组件属性时，可从已配置数据源填充相关属性。同时数据源变更时，该组件属性也随之变更。

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/6131d5e3b230691195e7ffe8e2cf158a.png)

### 3.1.9 定时调度

支持对已配置流水线/流水线组进行定时调度，调度采用Cron表达式进行设置，支持设置调度的开始时间和结束时间。

调度列表如下图所示，支持进入流水线/流水线组进行配置，支持编辑调度信息，启动调度、停止调度和删除调度。

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/74506b31ea2a9b14757b1383d5907443.png)

新建调度如下图所示。需选择调度的类型（Flow/FlowGroup），Cron表达式，调度开始时间，调度结束时间，以及被调度的流水线/流水线组。

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/a7ad4b6f8ad9ea4bd7b019dc0d7fe51c.png)

被调度成功的流水线会在Processor列表页显示。

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/6ce32509960f6ce33a48a8c52d2bbd35.png)

### 3.1.10 组件热插拔

支持上传自定义开发组件jar包，mount成功后流水线配置页面会自动显示自定义开发组件。Unmount后，自定义开发组件会消失。

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/3f7ba0f389717bf0da295ff4ccdc2553.png)

### 3.1.11 依赖包管理

支持上传Spark依赖的jar包，mount成功后运行流水线时会自动加载jar包。

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/aa3f92f8d2b247fbe522c6375c628e94.png)

### 3.1.12 测试数据管理

支持创建测试数据，包括定义Schema、手工录入数据和CSV导入数据。测试数据管理可支持右键运行Stop功能（详见3.1.4.4）。

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/331054a587b3c84e992f663700b25f61.png)

测试数据支持Manual和CSV导入两种方式

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/1cca1dbef9c3aa61f1083414dfd95fde.png)

手动录入模式，支持Schema定义和数据录入

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/867bf8b3751b2fb22c0601159ada2d74.png)

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/23f3085d3856920014ebdae487e8a037.png)

CSV导入模式支持带入CSV文件

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/d84d68e4c6ec6cdaa83e49edda9784f6.png)

### 3.1.12 数据处理组件显隐管理

支持设置数据处理组件的显示和隐藏，效果实时同步至流水线配置页面。

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V1.0/png/b39c91588796724aeb4213106591caae.png)

## 3.2 Restful API

接口采用REST设计风格，目前需求如下接口：

### 3.2.1 getAllGroups

| **基本信息**   |                                |                                          |          |
|----------------|--------------------------------|------------------------------------------|----------|
| 接口名称       | getAllGroups                   |                                          |          |
| 接口描述       | 获取所有数据处理组件Stop所在组 |                                          |          |
| 接口URL        | GET /stop/ groups              |                                          |          |
| **参数说明**   |                                |                                          |          |
| 名称           | 描述                           | 类型                                     | 数据类型 |
| 无             |                                |                                          |          |
| **返回值说明** |                                |                                          |          |
| 描述           | 返回代码                       | 实例                                     |          |
| 返回所有组信息 | 200                            | {“groups”:”Common,Hive,Http,…”}          |          |
|                | 500                            | “getGroup Method Not Implemented Error!” |          |

### 3.2.2 getAllStops

| **基本信息**   |                      |                                             |          |
|----------------|----------------------|---------------------------------------------|----------|
| 接口名称       | getAllStops          |                                             |          |
| 接口描述       | 获取所有数据处理组件 |                                             |          |
| 接口URL        | GET /stop/list       |                                             |          |
| **参数说明**   |                      |                                             |          |
| 名称           | 描述                 | 类型                                        | 数据类型 |
| 无             |                      |                                             |          |
| **返回值说明** |                      |                                             |          |
| 描述           | 返回代码             | 实例                                        |          |
| 返回所有Stop   | 200                  | {“stops”:”cn.PiFlow .bundle.Common.Fork,…”} |          |
|                | 500                  | “Can not found stop !”                      |          |

### 3.2.3 getStopInfo

|          |
|------------------|--------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|
|          |
|          |
|          |
|          |
| 数据类型 |
| String   |
|          |
|          |
| 返回Stop详细信息 | 200                            | {"name":"LoadFromFtp","bundle":"cn.PiFlow .bundle.ftp.LoadFromFtp",“groups”:"ftp,load","description":"load data from ftp server","properties":[{"property":{"name":"url_str","displayName":"URL","description":null,"defaultValue":"","allowableValues":"","required":"true","sensitive":"false"}},{"property":{"name":"port","displayName":"PORT","description":null,"defaultValue":"","allowableValues":"","required":"true","sensitive":"false"}},{"property":{"name":"username","displayName":"USER_NAME","description":null,"defaultValue":"","allowableValues":"","required":"true","sensitive":"false"}},{"property":{"name":"password","displayName":"PASSWORD","description":null,"defaultValue":"","allowableValues":"","required":"true","sensitive":"false"}},{"property":{"name":"ftpFile","displayName":"FTP_File","description":null,"defaultValue":"","allowableValues":"","required":"true","sensitive":"false"}},{"property":{"name":"localPath","displayName":"Local_Path","description":null,"defaultValue":"","allowableValues":"","required":"true","sensitive":"false"}}]} |          |
|                  | 500                            | “get PropertyDescriptor or |          |

### 3.2.4 startFlow

|
|----------------------|------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|
|
|
|
|
| Flow的json配置字符串 | String           | {"flow":{"name":"test","uuid":"1234","stops":[{"uuid":"1111","name":"XmlParser","bundle":"cn.PiFlow .bundle.xml.XmlParser","properties":{"xmlpath":"hdfs://10.0.86.89:9000/xjzhu/dblp.mini.xml","rowTag":"phdthesis"}},{"uuid":"2222","name":"SelectField","bundle":"cn.PiFlow .bundle.common.SelectField","properties":{"schema":"title,author,pages"}},{"uuid":"3333","name":"PutHiveStreaming","bundle":"cn.PiFlow .bundle.hive.PutHiveStreaming","properties":{"database":"sparktest","table":"dblp_phdthesis"}},{"uuid":"4444","name":"CsvParser","bundle":"cn.PiFlow .bundle.csv.CsvParser","properties":{"csvPath":"hdfs://10.0.86.89:9000/xjzhu/phdthesis.csv","header":"false","delimiter":",","schema":"title,author,pages"}},{"uuid":"555","name":"Merge","bundle":"cn.PiFlow .bundle.common.Merge","properties":{}},{"uuid":"666","name":"Fork","bundle":"cn.PiFlow .bundle.common.Fork","properties":{"outports":["out1","out2","out3"]}},{"uuid":"777","name":"JsonSave","bundle":"cn.PiFlow .bundle.json.JsonSave","properties":{"jsonSavePath":"hdfs://10.0.86.89:9000/xjzhu/phdthesis.json"}},{"uuid":"888","name":"CsvSave","bundle":"cn.PiFlow .bundle.csv.CsvSave","properties":{"csvSavePath":"hdfs://10.0.86.89:9000/xjzhu/phdthesis_result.csv","header":"true","delimiter":","}}],"paths":[{"from":"XmlParser","outport":"","inport":"","to":"SelectField"},{"from":"SelectField","outport":"","inport":"data1","to":"Merge"},{"from":"CsvParser","outport":"","inport":"data2","to":"Merge"},{"from":"Merge","outport":"","inport":"","to":"Fork"},{"from":"Fork","outport":"out1","inport":"","to":"PutHiveStreaming"},{"from":"Fork","outport":"out2","inport":"","to":"JsonSave"},{"from":"Fork","outport":"out3","inport":"","to":"CsvSave"}]} |
|
|
| 返回flow的appId      | 200              | |
|

### 3.2.5 stopFlow

| **基本信息**   |                 |                                |
|----------------|-----------------|--------------------------------|
| 接口名称       | stopFlow        |                                |
| 接口描述       | 停止流水线      |                                |
| 接口URL        | POST /flow/stop |                                |
| **参数说明**   |                 |                                |
| 描述           | 类型            | 实例                           |
| Flow的appID    | String          | {“appID”:”\*\*\*”}             |
| **返回值说明** |                 |                                |
| 描述           | 返回代码        | 实例                           |
| 返回执行状态   | 200             | “ok”                           |
|                | 500             | “Can not found process Error!” |

### 3.2.6 getFlowInfo

|          |
|------------------|-----------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|
|          |
|          |
|          |
|          |
| 数据类型 |
| String   |
|          |
|          |
| 返回Flow详细信息 | 200                         | {"flow":{"id":"application_1540442049798_0297","pid":"process_372bd7da-a53e-46b4-8c44-edc0463064f5_1","name":"xml,csv-merge-fork-hive,json,csv","state":"COMPLETED","startTime":"Tue Nov 27 14:37:03 CST 2018","endTime":"Tue Nov 27 14:37:28 CST 2018","stops":[{"stop":{"name":"JsonSave","state":"COMPLETED","startTime":"Tue Nov 27 14:37:24 CST 2018","endTime":"Tue Nov 27 14:37:28 CST 2018"}},{"stop":{"name":"CsvSave","state":"COMPLETED","startTime":"Tue Nov 27 14:37:20 CST 2018","endTime":"Tue Nov 27 14:37:24 CST 2018"}},{"stop":{"name":"PutHiveStreaming","state":"COMPLETED","startTime":"Tue Nov 27 14:37:13 CST 2018","endTime":"Tue Nov 27 14:37:20 CST 2018"}},{"stop":{"name":"Fork","state":"COMPLETED","startTime":"Tue Nov 27 14:37:13 CST 2018","endTime":"Tue Nov 27 14:37:13 CST 2018"}},{"stop":{"name":"Merge","state":"COMPLETED","startTime":"Tue Nov 27 14:37:11 CST 2018","endTime":"Tue Nov 27 14:37:11 CST 2018"}},{"stop":{"name":"SelectField","state":"COMPLETED","startTime":"Tue Nov 27 14:37:11 CST 2018","endTime":"Tue Nov 27 14:37:11 CST 2018"}},{"stop":{"name":"XmlParser","state":"COMPLETED","startTime":"Tue Nov 27 14:37:09 CST 2018","endTime":"Tue Nov 27 14:37:11 CST 2018"}},{"stop":{"name":"CsvParser","state":"COMPLETED","startTime":"Tue Nov 27 14:37:03 CST 2018","endTime":"Tue Nov 27 14:37:09 CST 2018"}}]}} |          |
|                  | 500                         | “appID is null or flow run |          |

### 3.2.7 getFlowProgress

| **基本信息**   |                                 |                                                                                                                                     |          |
|----------------|---------------------------------|-------------------------------------------------------------------------------------------------------------------------------------|----------|
| 接口名称       | getFlowProgress                 |                                                                                                                                     |          |
| 接口描述       | 获取流水线Flow的执行进度        |                                                                                                                                     |          |
| 接口URL        | GET /flow/progress?appID=\*\*\* |                                                                                                                                     |          |
| **参数说明**   |                                 |                                                                                                                                     |          |
| 名称           | 描述                            | 类型                                                                                                                                | 数据类型 |
| appID          | Flow的Id                        | Query                                                                                                                               | String   |
| **返回值说明** |                                 |                                                                                                                                     |          |
| 描述           | 返回代码                        | 实例                                                                                                                                |          |
| 返回Flow的进度 | 200                             | {"flow":{"appId":"application_1540442049798_0297","name":"xml,csv-merge-fork-hive,json,csv","state":"COMPLETED","progress":"100%"}} |          |
|                | 500                             | “appId is null or flow run failed!”                                                                                                 |          |

### 3.2.8 getFlowLog

|          |
|---------------------|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|
|          |
|          |
|          |
|          |
| 数据类型 |
| String   |
|          |
|          |
| 返回Flow的log的地址 | 200                        | {"app":{"id":"application_1540442049798_0297","user":"root","name":"xml,csv-merge-fork-hive,json,csv","queue":"default","state":"FINISHED","finalStatus":"SUCCEEDED","progress":100.0,"trackingUI":"History","trackingUrl":"http://master:8088/proxy/application_1540442049798_0297/A","diagnostics":"","clusterId":1540442049798,"applicationType":"SPARK","applicationTags":"","startedTime":1543300611067,"finishedTime":1543300648590,"elapsedTime":37523,"amContainerLogs":"http://master:8042/node/containerlogs/container_1540442049798_0297_01_000001/root","amHostHttpAddress":"master:8042","allocatedMB":-1,"allocatedVCores":-1,"runningContainers":-1,"memorySeconds":217375,"vcoreSeconds":105,"preemptedResourceMB":0,"preemptedResourceVCores":0,"numNonAMContainerPreempted":0,"numAMContainerPreempted":0}} |          |
|                     | 500                        | “appID is null or flow does |          |

### 3.2.9 getFlowCheckPoints

| **基本信息**          |                                    |                                         |          |
|-----------------------|------------------------------------|-----------------------------------------|----------|
| 接口名称              | getFlowCheckPoints                 |                                         |          |
| 接口描述              | 获取流水线Flow的checkPoints        |                                         |          |
| 接口URL               | GET /flow/checkpoints?appID=\*\*\* |                                         |          |
| **参数说明**          |                                    |                                         |          |
| 名称                  | 描述                               | 类型                                    | 数据类型 |
| appID                 | Flow的appID                        | Query                                   | String   |
| **返回值说明**        |                                    |                                         |          |
| 描述                  | 返回代码                           | 实例                                    |          |
| 返回Flow的checkpoints | 200                                | {"checkpoints":"Merge,Fork"}            |          |
|                       | 500                                | “appID is null or flow does not exist!” |          |

### 3.2.10 getFlowDebugData

| **基本信息**                                 |                                  |                                         |          |
|----------------------------------------------|----------------------------------|-----------------------------------------|----------|
| 接口名称                                     | getFlowDebugData                 |                                         |          |
| 接口描述                                     | 获取流水线Flow的调试数据         |                                         |          |
| 接口URL                                      | GET /flow/debugData?appID=\*\*\* |                                         |          |
| **参数说明**                                 |                                  |                                         |          |
| 名称                                         | 描述                             | 类型                                    | 数据类型 |
| appID                                        | Flow的appID                      | Query                                   | String   |
| stopName                                     | stop的名称                       | Query                                   | String   |
| Port                                         | Stop的端口名                     | Query                                   | String   |
| **返回值说明**                               |                                  |                                         |          |
| 描述                                         | 返回代码                         | 实例                                    |          |
| 返回Flow的指定stop和端口的调试数据的hdfs路径 | 200                              | {"schema":””, “debugDataPath”:" "}      |          |
|                                              | 500                              | “appID is null or flow does not exist!” |          |

### 3.2.11 startFlowGroup

|
|---------------------------|-------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|
|
|
|
|
| FlowGroup的json配置字符串 | String            | {"group":{"flows":[{"flow":{"executorNumber":"1","driverMemory":"1g","executorMemory":"1g","executorCores":"1","paths":[{"inport":"","from":"MockData","to":"ShowData","outport":""}],"name":"f4","stops":[{"customizedProperties":{},"name":"MockData","uuid":"8a80d63f720cdd2301723b7745b72649","bundle":"cn.PiFlow .bundle.common.MockData","properties":{"schema":"title:String,author:String,age:Int","count":"10"}},{"customizedProperties":{},"name":"ShowData","uuid":"8a80d63f720cdd2301723b7745b72647","bundle":"cn.PiFlow .bundle.external.ShowData","properties":{"showNumber":"5"}}],"uuid":"8a80d63f720cdd2301723b7745b62645"}},{"flow":{"executorNumber":"1","driverMemory":"1g","executorMemory":"1g","executorCores":"1","paths":[{"inport":"","from":"MockData","to":"ShowData","outport":""}],"name":"f3","stops":[{"customizedProperties":{},"name":"MockData","uuid":"8a80d63f720cdd2301723b7745b9265d","bundle":"cn.PiFlow .bundle.common.MockData","properties":{"schema":"title:String,author:String,age:Int","count":"10"}},{"customizedProperties":{},"name":"ShowData","uuid":"8a80d63f720cdd2301723b7745b9265b","bundle":"cn.PiFlow .bundle.external.ShowData","properties":{"showNumber":"5"}}],"uuid":"8a80d63f720cdd2301723b7745b82659"}}],"name":"SimpleGroup","groups":[{"group":{"flows":[{"flow":{"executorNumber":"1","driverMemory":"1g","executorMemory":"1g","executorCores":"1","paths":[{"inport":"","from":"MockData","to":"ShowData","outport":""}],"name":"MockData","stops":[{"customizedProperties":{},"name":"MockData","uuid":"8a80d63f720cdd2301723b7745b4261a","bundle":"cn.PiFlow .bundle.common.MockData","properties":{"schema":"title:String,author:String,age:Int","count":"10"}},{"customizedProperties":{},"name":"ShowData","uuid":"8a80d63f720cdd2301723b7745b32618","bundle":"cn.PiFlow .bundle.external.ShowData","properties":{"showNumber":"5"}}],"uuid":"8a80d63f720cdd2301723b7745b32616"}},{"flow":{"executorNumber":"1","driverMemory":"1g","executorMemory":"1g","executorCores":"1","paths":[{"inport":"","from":"MockData","to":"ShowData","outport":""}],"name":"MockData","stops":[{"customizedProperties":{},"name":"MockData","uuid":"8a80d63f720cdd2301723b7745b5262e","bundle":"cn.PiFlow .bundle.common.MockData","properties":{"schema":"title:String,author:String,age:Int","count":"10"}},{"customizedProperties":{},"name":"ShowData","uuid":"8a80d63f720cdd2301723b7745b5262c","bundle":"cn.PiFlow .bundle.external.ShowData","properties":{"showNumber":"5"}}],"uuid":"8a80d63f720cdd2301723b7745b4262a"}}],"name":"g1","uuid":"8a80d63f720cdd2301723b7745b22615"}}],"conditions":[{"entry":"f4","after":"g1"},{"entry":"f3","after":"g1"}],"uuid":"8a80d63f720cdd2301723b7745b22614"}} |
|
|
| 返回flowGroup的Id         | 200               | |
|

### 3.2.12 stopFlowGroup

| **基本信息**              |                  |                                  |
|---------------------------|------------------|----------------------------------|
| 接口名称                  | stopFlowGroup    |                                  |
| 接口描述                  | 停止流水线组     |                                  |
| 接口URL                   | POST /group/stop |                                  |
| **参数说明**              |                  |                                  |
| 描述                      | 类型             | 实例                             |
| FlowGroup的json配置字符串 | String           | {“groupId”:”\*\*\*”}             |
| **返回值说明**            |                  |                                  |
| 描述                      | 返回代码         | 实例                             |
| 返回停止操作的状态        | 200              | “Stop FlowGroup OK!!!”           |
|                           | 500              | “Can not found FlowGroup Error!” |

### 3.2.13 getFlowGroupInfo

|
|----------------|--------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|
|
|
|
|
|
|
|
| 返回group信息  | 200                            | {"group":{"name":"SimpleGroup","startTime":"FriMay2918:10:50CST2020","state":"STARTED","flows":[],"groups":[{"group":{"name":"g1","startTime":"FriMay2918:10:50CST2020","state":"COMPLETED","flows":[{"flow":{"name":"MockData","startTime":"FriMay2918:11:03CST2020","state":"COMPLETED","endTime":"FriMay2918:11:07CST2020","id":"application_1589249052248_0440","pid":"process_b3c96bf0-c9b4-41b1-b0e0-06fb2d5e4be5_1","progress":"100","stops":[{"stop":{"name":"ShowData","state":"COMPLETED","startTime":"FriMay2918:11:07CST2020","endTime":"FriMay2918:11:07CST2020"}},{"stop":{"name":"MockData","state":"COMPLETED","startTime":"FriMay2918:11:03CST2020","endTime":"FriMay2918:11:07CST2020"}}]}}],"groups":[],"endTime":"FriMay2918:11:20CST2020","id":"group_2322a41d-7b69-4fe7-9a87-a78c50f26e09"}}],"endTime":"","id":"group_0a7abbd3-9c9a-4dfa-9a0b-7f77fdacf3d4"}} |
|                | 500                            | “Can not found FlowGroup |

### 3.2.14 getFlowGroupProgress

| **基本信息**   |                                    |                                                    |
|----------------|------------------------------------|----------------------------------------------------|
| 接口名称       | getFlowGroupProgress               |                                                    |
| 接口描述       | 获取流水线group的执行进度          |                                                    |
| 接口URL        | GET /group/progress?groupId=\*\*\* |                                                    |
| **参数说明**   |                                    |                                                    |
| 名称           | 描述                               | 类型                                               |
| groupId        | Group的id                          | String                                             |
| **返回值说明** |                                    |                                                    |
| 描述           | 返回代码                           | 实例                                               |
| 返回执行进度   | 200                                | “100”                                              |
|                | 500                                | “groupId is null or flowGroup progress exception!” |
