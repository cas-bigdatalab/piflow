# Common

## 1.11AddUUIDStop

增加UUID列

### 1.1.1 port

Inport：默认端口

outport：默认端口

### 1.1.2 properties

| 名称   | 展示名称 | 默认值 | 允许值 | 是否必填 | 描述                   | 例子 |
|--------|----------|--------|--------|----------|------------------------|------|
| column | Column   | “uuid” | 无     | 是       | 你想要添加的uuid的列名 | uuid |

## 1.2 ConvertSchema

更换字段名称

### 1.2.1 Port

inport：默认端口

outport：默认端口

### 1.2.2 Properties

| 名称   | 展示名称 | 默认值 | 允许值 | 是否必填 | 描述                                       | 例子                                                              |
|--------|----------|--------|--------|----------|--------------------------------------------|-------------------------------------------------------------------|
| schema | Schema   | “”     | 无     | 是       | 需要修改的字段名称，多个列名之间用逗号隔开 | id-\>uuid, name-\> authorname(箭头之前是旧字段，箭头之后是新字段) |

## 1.3 Distinct

基于指定的列名或所有列名去重

### 1.3.1 Port

Inport：默认端口

outport：默认端口

### 1.3.2 Properties

| 名称        | 展示名称    | 默认值 | 允许值 | 是否必填 | 描述                                                       | 例子    |
|-------------|-------------|--------|--------|----------|------------------------------------------------------------|---------|
| columnNames | ColumnNames | “”     | 无     | 是       | 填写要去重的列名，多个列名之间用逗号分隔，否则将删除所有列 | id,name |

## 1.4 DropField

删除一列或多列

### 1.4.1 port

Inport：默认端口

outport：默认端口

### 1.4.2 properties

| 名称        | 展示名称    | 默认值 | 允许值 | 是否必填 | 描述                                   | 例子    |
|-------------|-------------|--------|--------|----------|----------------------------------------|---------|
| columnNames | ColumnNames | “”     | 有     | 是       | 填写要删除的列，多个列名之间用逗号分隔 | id,name |

## 1.5 ExecuteSQLStop

创建临时视图表以执行sql

### 1.5.1 port

Inport：默认端口

outport：默认端口

### 1.5.2 properties

| 名称     | 展示名称 | 默认值 | 允许值 | 是否必填 | 描述             | 例子                |
|----------|----------|--------|--------|----------|------------------|---------------------|
| sql      | Sql      | “”     | 无     | 是       | 执行的sql语句    | Select \* from temp |
| Viewname | ViewName | “temp” | 有     | 否       | 临时视图表的名称 | temp                |

## 1.7 Filter

通过条件过滤

### 1.7.1 port

Inport：默认端口

outport：默认端口

### 1.7.2 properties

| 名称      | 展示名称  | 默认值 | 允许值 | 是否必填 | 描述           | 例子                                                          |
|-----------|-----------|--------|--------|----------|----------------|---------------------------------------------------------------|
| condition | Condition | “”     | 有     | 是       | 想要过滤的条件 | name==’zhangsan’ (name是过滤的条件字段，zhangsan是过滤的条件) |

## 1.8 Fork

将数据分流给不同的stop

### 1.8.1 port

Inport：默认端口

outport：任意端口

### 1.8.2 properties

| 名称     | 展示名称 | 默认值 | 允许值 | 是否必填 | 描述                       | 例子          |
|----------|----------|--------|--------|----------|----------------------------|---------------|
| outports | OutPorts | “”     | 无     | 是       | 输出端口，多端口用逗号分隔 | out1,out2,... |

## 1.9 Join

表连接包括完全连接、左连接、右连接和内部连接

### 1.9.1 port

Inport：左端口，右端口

DefaultPort：默认端口

### 1.9.2 properties

| 名称             | 展示名称         | 默认值 | 允许值 | 是否必填 | 描述                                      | 例子                            |
|------------------|------------------|--------|--------|----------|-------------------------------------------|---------------------------------|
| joinMode         | JoinMode         | “”     | 有     | 是       | 对于表关联，可以选择inner,left,right,full | left                            |
| correlationField | CorrelationField | “”     | 有     | 是       | 与表关联的列（如果多个列用逗号分隔）      | id,name(表之间相关联的列的名称) |

## 1.10 Merge

将数据合并到一个stop

### 1.10.1 port

Inport：任何端口

DefaultPort：默认端口

### 1.10.2 properties

| 名称    | 展示名称 | 默认值 | 允许值 | 是否必填 | 描述                       | 例子        |
|---------|----------|--------|--------|----------|----------------------------|-------------|
| inports | Inports  | “”     | 无     | 是       | 输入端口，多端口用逗号分隔 | in1,in2,... |

## 1.11 MockData

模拟测试数据

### 1.11.1 Port

Inport：默认端口

outport：默认端口

### 1.11.2 properties

| 名称   | 展示名称 | 默认值 | 允许值 | 是否必填 | 描述                                                                                                                                                   | 例子                                  |
|--------|----------|--------|--------|----------|--------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------|
| schema | Schema   | “”     | 无     | 是       |  模拟数据的schema，schema的格式为column:columnType:isNullable。columnType可以是String/Int/Long/Float/Double/Boolean。isNullable可以为空，默认值为false | name:String,age:Int,isStudent:Boolean |
| count  | Count    | “”     | 无     | 是       | 测试数据的数量                                                                                                                                         | 10                                    |

## 1.12 Route

按自定义属性路由数据，键是端口，值是筛选器

### 1.12.1 port

Inport：默认端口

RoutePort：路由端口

### 1.12.2 properties

| 名称 | 展示名称 | 默认值 | 允许值 | 是否必填 | 描述 |
|------|----------|--------|--------|----------|------|
|      |          |        |        |          |      |

## 1.13 SelectField

选择需要的数据列

### 1.13.1 port

Inport：默认端口

outport：默认端口

### 1.13.2 properties

| 名称         | 展示名称    | 默认值 | 允许值 | 是否必填 | 描述                           | 例子     |
|--------------|-------------|--------|--------|----------|--------------------------------|----------|
| columnNames  | ColumnNames | “”     | 无     | 是       | 选择所需的列，多个列用逗号分隔 | id，name |

## 1.14 Subtract

去除两表重复项

### 1.14.1 port

Inport：左端口，右端口

outport：默认端口

### 1.14.2 properties

| 名称 | 展示名称 | 默认值 | 允许值 | 是否必填 | 描述 |
|------|----------|--------|--------|----------|------|
|      |          |        |        |          |      |

# 2. Data Clean

## 2.1 EmailClean

邮箱号清洗

### 2.1.1 port

Inport：默认端口

outport：默认端口

### 2.1.2 properties

| 名称      | 展示名称    | 默认值 | 允许值 | 是否必填 | 描述                            | 例子  |
|-----------|-------------|--------|--------|----------|---------------------------------|-------|
| columName | Column Name | “”     | 无     | 是       | 需要清洗的字段名,多列以逗号分隔 | email |

## 2.2 IdentityNumberClean

身份证号清洗

### 2.2.1 port

Inport：默认端口

outport：默认端口

### 2.2.2 properties

| 名称      | 展示名称    | 默认值 | 允许值 | 是否必填 | 描述                            | 例子   |
|-----------|-------------|--------|--------|----------|---------------------------------|--------|
| columName | Column Name | “”     | 无     | 是       | 需要清洗的字段名,多列以逗号分隔 | IdCard |

## 2.3 PhoneNumberClean

手机号清洗

### 2.3.1 port

Inport：默认端口

outport：默认端口

### 2.3.2 properties

| 名称      | 展示名称   | 默认值 | 允许值 | 是否必填 | 描述             | 例子        |
|-----------|------------|--------|--------|----------|------------------|-------------|
| columName | COLUM_NAME | “”     | 无     | 是       | 需要清洗的字段名 | phoneNumber |

## 2.4 TitleClean

标题清洗

### 2.4.1 port

Inport：默认端口

outport：默认端口

### 2.4.2 properties

| 名称      | 展示名称    | 默认值 | 允许值 | 是否必填 | 描述                            | 例子  |
|-----------|-------------|--------|--------|----------|---------------------------------|-------|
| columName | Column Name | “”     | 无     | 是       | 需要清洗的字段名,多列以逗号分隔 | Title |

## 2.4 ProvinceClean

省份清洗

### 2.4.1 port

Inport：默认端口

outport：默认端口

### 2.4.2 properties

| 名称      | 展示名称    | 默认值 | 允许值 | 是否必填 | 描述                            | 例子     |
|-----------|-------------|--------|--------|----------|---------------------------------|----------|
| columName | Column Name | “”     | 无     | 是       | 需要清洗的字段名,多列以逗号分隔 | province |

# 3. CSV

## 3.1 CsvParser

解析csv文件或文件夹

### 3.1.1port

inport：默认端口

outport：默认端口

### 3.1.2properties

| 名称      | 展示名称  | 默认值 | 允许值 | 是否必填 | 描述               | 例子                                   |
|-----------|-----------|--------|--------|----------|--------------------|----------------------------------------|
| csvPath   | CsvPath   | “”     | 无     | 是       | 文件地址           | hdfs://master:9000/test/               |
| header    | Header    | “”     | 无     | 是       | 是否包含文件头信息 | true(表示有头信息,false表示没有头信息) |
| delimiter | Delimiter | “”     | 无     | 是       | 文件分割符号       | “,”                                    |
| schame    | Schame    | “”     | 无     | 否       | 字段描述信息       | Id,name,...                            |

## 3.2 CsvSave

保存到csv文件

### 3.2.1port

inport：默认端口

outport：默认端口

### 3.2.2properties

| 名称        | 展示名称    | 默认值   | 允许值 | 是否必填 | 描述               | 例子                                                                                                |
|-------------|-------------|----------|--------|----------|--------------------|-----------------------------------------------------------------------------------------------------|
| csvSavePath | CsvSavePath | “”       | 无     | 是       | 文件保存路径       | hdfs://master:9000/test/                                                                            |
| header      | Header      | “”       | 无     | 是       | 是否包含文件头信息 | true(表示有头信息,false表示没有头信息)                                                              |
| delimiter   | Delimiter   | “”       | 无     | 是       | 文件分割符号       | “,”                                                                                                 |
| saveMode    | saveMode    | “append” | 有     | 是       | 保存csv文件的模式  | append：追加 overwrite：覆盖 Ignore：如果存在则忽略 ErrorIfExists：如果已经存在数据，则将引发异常。 |

## 3.3 CsvStringParser

解析csv字符串

### 3.3.1port

inport：默认端口

outport：默认端口

### 3.3.2properties

| 名称      | 展示名称  | 默认值 | 允许值 | 是否必填 | 描述         | 例子          |
|-----------|-----------|--------|--------|----------|--------------|---------------|
| str       | String    | “”     | 无     | 是       | Csv字符串    | 1,zs 2,ls ... |
| schema    | Schema    | “”     | 无     | 否       | 字段描述信息 | Id,name       |
| delimiter | Delimiter | “”     | 无     | 是       | 文件分割符号 | “,”           |

# 4.ElasticSearch

## 4.1 PutElasticSearch

写入 ElasticSearch

### 4.1.1 Port

inport：默认端口

outport：默认端口

### 4.1.2 properties

| 名称               | 展示名称            | 默认值 | 允许值 | 是否必填 | 描述   | 例子                           |
|--------------------|---------------------|--------|--------|----------|--------|--------------------------------|
| es_nodes           | Es\_Nodes           | “”     | 无     | 是       | Es的ip | master                         |
| es_port            | Es\_Port            | 9200   | 无     | 是       | 端口号 | 9200                           |
| es_index           | Es\_Index           | “”     | 无     | 是       | 索引   | testdb(类比关系型数据库里的DB) |
| es_type            | Es\_Type            | “”     | 无     | 是       | 类型   | user(类比关系数据库里的Table)  |
| configuration_item | Configuration\_Item |        | 无     | 是       | 配置项 | es.mapping.parent-\>id_1       |

## 4.2 QueryElasticSearch

>   从ElasticSearch 查询数据

### 4.2.1 Port

>   inport：默认端口

>   outport：默认端口

### 4.2.2 properties

| **名称** | **展示名称** | **默认值** | **允许值** | **是否必填** | **描述**               | **例子**                           |
|----------|--------------|------------|------------|--------------|------------------------|------------------------------------|
| es_nodes | Es\_Nodes    | “”         | 无         | 是           | Es的ip，多个用逗号分隔 | 127.0.0.1                          |
| es_port  | Es\_Port     | 9200       | 无         | 是           | 端口号                 | 9200                               |
| es_index | Es\_Index    | “”         | 无         | 是           | 索引                   | testdb(类比关系型数据库里的DB)     |
| es_type  | Es\_Type     | “”         | 无         | 是           | 类型                   | user(类比关系数据库里的Table)      |
| jsonDSL  | JsonDSL      | “”         | 无         | 是           | 查询语句               | {\\"query\\":{\\"match_all\\":{}}} |

# 5.File

## 5.1 GetFile

从hdfs获取文件到本地

### 5.1.1 port

Inport：默认端口

outport：默认端口

### 5.1.2 properties

| 名称      | 展示名称  | 默认值 | 允许值 | 是否必填 | 描述                     | 例子           |
|-----------|-----------|--------|--------|----------|--------------------------|----------------|
| ip        | IP        | “”     | 无     | 是       | 本地文件所在的服务器IP   | master         |
| user      | User      |        | 无     | 是       | 本地文件所在的服务器用户 | root           |
| passWord  | PassWord  |        | 无     | 是       | 本地文件所在服务器的密码 | 123456         |
| hdfsFile  | HdfsFile  |        | 无     | 是       | hdfs上的文件路径         | /work/test.csv |
| localPath | LocalPath |        | 无     | 是       | 本地路径                 | /opt/          |

## 5.2 PutFile

上传本地文件到hdfs

### 5.2.1 port

Inport：默认端口

outport：默认端口

### 5.2.2 properties

| 名称      | 展示名称  | 默认值 | 允许值 | 是否必填 | 描述                     | 例子           |
|-----------|-----------|--------|--------|----------|--------------------------|----------------|
| ip        | IP        | “”     | 无     | 是       | 本地文件所在的服务器IP   | master         |
| user      | User      |        | 无     | 是       | 本地文件所在的服务器用户 | root           |
| PassWord  | PassWord  |        | 无     | 是       | 本地文件所在服务器的密码 | 123456         |
| hdfsFile  | HdfsFile  |        | 无     | 是       | hdfs上的文件路径         | /work/test.csv |
| localPath | LocalPath |        | 无     | 是       | 本地路径                 | /opt/          |

## 5.3 RegexTextProcess

用正则表达式替换或者过滤指定列的每一个值

### 5.3.1 port

Inport：默认端口

outport：默认端口

### 5.3.2 properties

| 名称       | 展示名称     | 默认值 | 允许值 | 是否必填 | 描述             | 例子 |
|------------|--------------|--------|--------|----------|------------------|------|
| regex      | Regex        | “”     | 无     | 是       | 正则表达式       | 0001 |
| columnName | Column\_Name |        | 无     | 是       | 需要处理的字段名 | id   |
| replaceStr | Replace_Str  |        | 无     | 是       | 替换字符串       | 1111 |

# ftp

## 6.1 loadFromFtpUrl

>   下载ftp服务器文件保存到 hdfs 上

### 6.1.1 Port

>   inport：默认端口

>   outport：默认端口

### 6.1.2 properties

| **名称**     | **展示名称** | **默认值** | **允许值** | **是否必填** | **描述**                                                                                                                                                                                               | **例子**    |
|--------------|--------------|------------|------------|--------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------|
| ftp\_url     | Ftp\_Url     |            |            | 是           | ftp的IP地址                                                                                                                                                                                            | 128.136.0.1 |
| port         | Port         |            |            | 否           | ftp的端口                                                                                                                                                                                              |             |
| username     | UserName     |            |            | 否           | 用户名                                                                                                                                                                                                 |             |
| password     | Password     |            |            | 否           | 密码                                                                                                                                                                                                   |             |
| ftpFile      | FtpFile      |            |            | 是           | ftp文件路径                                                                                                                                                                                            |             |
| HDFSUrl      | HDFSUrl      |            |            | 是           | Hdfs的url地址                                                                                                                                                                                          |             |
| HDFSPath     | HDFSPath     | /          |            | 是           | 文件保存路径                                                                                                                                                                                           |             |
| isFile       | IsFile       |            |            | 是           | 是否是单个文件,如果为true，则仅下载由路径指定的单个文件。如果为false，则递归下载文件夹中的所有文件                                                                                                     |             |
| filterByName | FilterByName |            |            | 否           | 如果选择下载整个目录，则可以使用此参数筛选需要下载的文件。 这里需要填写一个标准的Java正则表达式。例如，您需要下载以/A/目录结尾的所有文件，您可以在这里填写.\*.gz。如果有多个过滤器，它们需要用逗号分隔 |             |

## 6.2 UpLoadToFtp

>   向ftp服务器上上传文件

### 6.2.1 Port

>   inport：默认端口

>   outport：默认端口

### 6.2.2 properties

| **名称**  | **展示名称** | **默认值** | **允许值** | **是否必填** | **描述**     |
|-----------|--------------|------------|------------|--------------|--------------|
| url_str   | Url\_Str     |            |            | 是           | ftp的ip地址  |
| port      | Port         |            |            | 是           | ftp的端口    |
| username  | UserName     |            |            | 是           | 用户名       |
| password  | Password     |            |            | 是           | 密码         |
| ftpFile   | FtpFile      |            |            | 是           | ftp文件路径  |
| localPath | LocalPath    | /          |            | 是           | 本地文件路径 |

# HBase

## 7.1 GetHbase

>   从Hbase读取数据

### Port

>   inport：默认端口

>   outport：默认端口

### 7.1.2 properties

| **名称**    | **展示名称** | **默认值** | **允许值** | **是否必填** | **描述**                       | **例子**                         |
|-------------|--------------|------------|------------|--------------|--------------------------------|----------------------------------|
| quorum      | quorum       |            |            | 是           | Zookeeper的集群地址            | 10.0.0.101,10.0.0.102,10.0.1.103 |
| port        | port         |            |            | 是           | Zookeeper的连接端口            | 2181                             |
| znodeParent | znodeParent  |            |            | 是           | Hbase znode在zookeeper中的位置 | /hbase-unsecure                  |
| table       | table        |            |            | 是           | Hbase中的表名                  | student                          |
| rowid       | rowid        |            |            | 是           | 表的rowkey                     | id                               |
| family      | family       |            |            | 是           | 表的列簇                       | info                             |
| qualifier   | qualifier    |            |            | 是           | 列簇字段，按列簇顺序填写       | Name,gender,age                  |

## 7.2 PutHbase

>   将数据写入 hbase

### 7.2.1 Port

>   inport：默认端口

>   outport：默认端口

### 7.2.2 properties

| **名称**    | **展示名称** | **默认值** | **允许值** | **是否必填** | **描述**                             | **例子**                         |
|-------------|--------------|------------|------------|--------------|--------------------------------------|----------------------------------|
| quorum      | quorum       |            |            | 是           | Zookeeper的集群地址                  | 10.0.0.101,10.0.0.102,10.0.1.103 |
| port        | port         |            |            | 是           | Zookeeper的连接端口                  | 2181                             |
| znodeParent | znodeParent  |            |            | 是           | Hbase znode在zookeeper中的位置       | /hbase-unsecure                  |
| outPutDir   | outPutDir    |            |            | 是           | Hbase临时工作区，作业输出路径        | /tmp                             |
| table       | table        |            |            | 是           | Hbase中的表名                        | student                          |
| rowid       | rowid        |            |            | 是           | hive中的表Id, Hbase中的表Rowkey      | id                               |
| family      | family       |            |            | 是           | 表的列簇, 只允许一个                 | info                             |
| qualifier   | qualifier    |            |            | 是           | 列簇的字段，在hive表中包含唯一id的列 | Name,gender,age                  |

# Hdfs

## 8.1 PutHdfs

>   将dataFrame的数据写入 hdfs

### 8.1.1 Port

>   inport：默认端口

>   outport：默认端口

### 8.1.2 properties

| **名称**  | **展示名称** | **默认值** | **允许值**       | **是否必填** | **描述**                        | **例子**           |
|-----------|--------------|------------|------------------|--------------|---------------------------------|--------------------|
| hdfsUrl   | HdfsUrl      |            |                  | 是           | Hdfs的Url地址                   | hdfs://master:8020 |
| hdfsPath  | HdfsPath     | /          |                  | 是           | Hdfs的路径                      | /work/test/        |
| partition | Partition    | 3          |                  | 是           | 分区，写成几个文件              | 2                  |
| types     | Types        | csv        | json,scv,parquet | 是           | 保存文件类型:Json，csv，parquet | csv                |

## 8.2 GetHdfs

>   获取hdfs的数据

### 8.2.1 Port

>   inport：默认端口

>   outport：默认端口

### 8.2.2 properties

| **名称** | **展示名称** | **默认值** | **允许值**           | **是否必填** | **描述**       | **例子**           |
|----------|--------------|------------|----------------------|--------------|----------------|--------------------|
| hdfsUrl  | HdfsUrl      |            |                      | 是           | Hdfs的Url地址  | hdfs://master:8020 |
| hdfsPath | HdfsPath     |            |                      | 是           | Hdfs的路径     | /work/test/        |
| types    | Types        | csv        | json,scv,parquet,txt | 是           | 下载的文件类型 | csv                |

## 8.3 ListHdfs

从hdfs检索文件列表

### 8.3.1 Port

>   inport：默认端口

>   outport：默认端口

### 8.3.2 properties

| **名称** | **展示名称** | **默认值** | **允许值** | **是否必填** | **描述**      | **例子**           |
|----------|--------------|------------|------------|--------------|---------------|--------------------|
| hdfsUrl  | HdfsUrl      |            |            | 是           | Hdfs的Url地址 | hdfs://master:8020 |
| hdfsPath | HdfsPath     |            |            | 是           | Hdfs的路径    | /work/             |

## 8.4 DeleteHdfs

>   删除hdfs指定文件或者文件夹

### 8.4.1 Port

>   inport：默认端口

>   outport：默认端口

### 8.4.2 properties

| **名称**    | **展示名称** | **默认值** | **允许值** | **是否必填** | **描述**                                                                                                        | **例子**           |
|-------------|--------------|------------|------------|--------------|-----------------------------------------------------------------------------------------------------------------|--------------------|
| hdfsUrl     | HdfsUrl      |            | 无         | 是           | Hdfs的Url地址                                                                                                   | hdfs://master:8020 |
| hdfsPath    | hdfsPath     |            | 无         | 是           | Hdfs的路径                                                                                                      | /work/test/        |
| isCustomize | IsCustomize  | true       | 有         | 否           | 是否自定义压缩文件路径，如果为true，则必须指定压缩文件所在的路径。如果为false，则从上游端口自动查找文件路径数据 | true               |

## 8.5 SelectFileByName

>   根据名字选择文件

### 8.5.1 Port

>   inport：默认端口

>   outport：默认端口

### 8.5.2 properties

| **名称**            | **展示名称**        | **默认值** | **允许值** | **是否必填** | **描述**                             | **例子**           |
|---------------------|---------------------|------------|------------|--------------|--------------------------------------|--------------------|
| hdfsUrl             | HdfsUrl             |            | 无         | 是           | Hdfs的Url地址                        | hdfs://master:8020 |
| Hdfspath            | Hdfspath            |            | 无         | 是           | Hdfs的路径                           | /work/             |
| SelectionConditions | SelectionConditions |            | 无         | 是           | 要选择条件，需要用java填充正则表达式 | .\*.csv            |

## 8.6 UnzipFilesOnHDFS

>   解压文件

### 8.6.1 Port

>   inport：默认端口

>   outport：默认端口

### 7.6.2 properties

| **名称**    | **展示名称** | **默认值** | **允许值** | **是否必填** | **描述**                                                                                                             | **例子**               |
|-------------|--------------|------------|------------|--------------|----------------------------------------------------------------------------------------------------------------------|------------------------|
| hdfsUrl     | HdfsUrl      | “”         | 无         | 是           | Hdfs的Url地址                                                                                                        | hdfs://master:8020     |
| savePath    | SavePath     | “”         | 无         | 是           | 此参数可以指定解压文件的位置，可以选择不填写，程序默认将解压文件保存在源文件所在的文件夹中。如果填写，可以指定文件夹 | /work/test/            |
| isCustomize | IsCustomize  |            |            | 否           | 是否自定义压缩文件路径，如果为true，则必须指定压缩文件所在的路径。如果为false，它将自动从上游端口找到文件路径数据    | true                   |
| filePath    | FilePath     |            |            | 否           | Hdfs的文件路径                                                                                                       | /work/test/test.tar.gz |

## 8.7FileDownHdfs

将数据从url下载到HDFS

### 8.6.1 Port

>   inport：默认端口

>   outport：默认端口

### 8.6.2 properties

| 名称     | 展示名称 | 默认值 | 允许值 | 是否必填 | 描述           | 例子                                     |
|----------|----------|--------|--------|----------|----------------|------------------------------------------|
| hdfsUrl  | HdfsUrl  | “”     | 无     | 是       | Hdfs的Url地址  | hdfs://master:8020                       |
| hdfsPath | HdfsPath | “”     | 无     | 是       | hdfs路径       | /work/dblp/dblp.xml.gz                   |
| url_str  | Url_Str  | “”     | 无     | 否       | 文件的网络地址 | https://dblp.dagstuhl.de/xml/dblp.xml.gz |

## 8.8 SaveToHdfs

将数据放到HDFS

### 8.8.1 Port

>   inport：默认端口

>   outport：默认端口

### 8.8.2 properties

| **名称**    | **展示名称** | **默认值** | **允许值** | **是否必填** | **描述**                           | **例子**           |
|-------------|--------------|------------|------------|--------------|------------------------------------|--------------------|
| hdfsUrl     | HdfsUrl      | “”         | 无         | 是           | Hdfs的Url地址                      | hdfs://master:8020 |
| hdfsDirPath | HdfsDirPath  | “”         | 无         | 是           | hdfs路径                           | /work/test/        |
| fileName    | FileName     | “”         | 无         | 否           | 文件的网络地址                     | test.csv           |
| types       | Types        | csv        | 有         | 是           | 想要写入的格式有json，csv，parquet | csv                |
| delimiter   | Delimiter    | “,”        | 无         | 是           | 设置csv文件类型的分隔符            | “,”                |
| header      | Header       | true       | 无         | 是           | Csv文件是否带表头                  | true               |

# Hive

## 9.1 PutHiveQL

执行hiveQL文件

### 9.1.1port

inport：默认端口

outport： 默认端口

### 9.1.2properties

| 名称         | 展示名称     | 默认值 | 允许值 | 是否必填 | 描述                           | 例子                                |
|--------------|--------------|--------|--------|----------|--------------------------------|-------------------------------------|
| HiveQL\_Path | HiveQL\_Path | “”     | 无     | 是       | Hiveql文件路径                 | hdfs://master:8020/test/Puthive.hql |
| Database     | Database     | ““     | 无     | 是       | hiveQL将在其上执行的数据库名称 | test                                |

## 9.2 PutHiveStreaming

写数据到Hive表

### port

inport：默认端口

outport：默认端口

### properties

| 名称     | 展示名称 | 默认值 | 允许值 | 是否必填 | 描述       | 例子 |
|----------|----------|--------|--------|----------|------------|------|
| Database | Database | ““     | 无     | 是       | 数据库名称 | test |
| Table    | Table    | ““     | 无     | 是       | 数据库表名 | user |

## 9.3 PutHiveMode

保存数据到hive的模式

### 9.3.1 port

inport： 默认端口

outport： 默认端口

### 9.3.2 properties

| 名称     | 展示名称 | 默认值   | 允许值 | 是否必填 | 描述           | 例子                                                                                                |
|----------|----------|----------|--------|----------|----------------|-----------------------------------------------------------------------------------------------------|
| Database | Database | ““       | 无     | 是       | 数据库名称     | test                                                                                                |
| Table    | Table    | ““       | 无     | 是       | 数据库表名     | user                                                                                                |
| saveMode | SaveMode | “append” | 有     | 是       | 保存数据的模式 | append：追加 overwrite：覆盖 Ignore：如果存在则忽略 ErrorIfExists：如果已经存在数据，则将引发异常。 |

## 9.4 SelectHiveQL

执行Hive的select语句

### 9.4.1 port

inport： 默认端口

outport： 默认端口

### 9.4.2 properties

| 名称   | 展示名称 | 默认值 | 允许值 | 是否必填 | 描述     | 例子                     |
|--------|----------|--------|--------|----------|----------|--------------------------|
| HiveQL | HiveQL   | ““     | 无     | 是       | Hive语句 | Select \* from test.user |

## 9.5 SelectHiveQLByJDBC

某些hive只能通过jdbc实现，此stop是为此而设计的

### 9.5.1 port

inport： 默认端口

outport： 默认端口

### 9.5.2 properties

| 名称         | 展示名称     | 默认值 | 允许值 | 是否必填 | 描述                  | 例子                      |
|--------------|--------------|--------|--------|----------|-----------------------|---------------------------|
| hiveUser     | HiveUser     | ““     | 无     | 是       | 连接Hive的用户        | root                      |
| hivePassword | HivePassword | “”     | 无     | 是       | 连接Hive的用户密码    | 123456                    |
| jdbcUrl      | JdbcUrl      | “”     | 无     | 是       | 通过JDBC连接hive的Url | jdbc:hive2://master:10000 |
| sql          | Sql          | “”     | 无     | 是       | Sql查询语句           | Select \* from test.user  |

#  Http

## 10.3 GetUrl

>   Get请求方式获取url的数据，写入dataframe

### 10.3.1 Port

>   inport：默认端口

>   outport：默认端口

### 10.3.2 properties

| 名称            | 展示名称        | 默认值 | 允许值   | 是否必填 | 描述               | 例子                                                                                  |
|-----------------|-----------------|--------|----------|----------|--------------------|---------------------------------------------------------------------------------------|
| url             | Url             | “”     |          | 是       | HTTP请求的url 地址 | https://api.elsevier.com/content/search/scopus?query=TITLE('title')&apiKey=555637gxd  |
| httpAcceptTypes | HttpAcceptTypes | “json” | Json,xml | 是       | 接收的url 数据类型 | json                                                                                  |
| label           | label           | “”     |          | Xml 必填 | 要解析的xml标签    | id,name                                                                               |
| schema          | Schema          | “”     |          | Xml 必填 | 保存的schema类型   | pid,authorname                                                                        |

## 10.4 PostUrl

>   Post请求方式发送数据到 url

### 10.4.1 Port

>   inport：默认端口

>   outport：默认端口

### 10.4.2 properties

| **名称** | **展示名称** | **默认值** | **允许值** | **是否必填** | **描述**               | **例子**                           |
|----------|--------------|------------|------------|--------------|------------------------|------------------------------------|
| url      | Url          | “”         |            | 是           | HTTP请求的url 地址     | http://10.0.86.98:8002/flow/start  |
| jsonPath | JsonPath     |            |            | 是           | 发送的json数据hdfs路径 | hdfs://master:9000/yg/flow.json    |

# Neo4J

## 11.1 HiveTo[Neo4](https://github.com/cas-bigdatalab/piflow/blob/master/piflow-bundle/src/main/scala/cn/piflow/bundle/neo4j/PutNeo4j.scala)

写入数据到neo4j

### 11.1.1 port

Inport：默认端口

outport：默认端口

### 11.1.2 properties

| 名称        | 展示名称    | 默认值 | 允许值 | 是否必填 | 描述                     | 例子                                                                                                                                                                                                                     |
|-------------|-------------|--------|--------|----------|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| hiveQL      | HiveQL      | “”     | 无     | 是       | Hive保存到neo4j的sql语句 | Select \* from test.user                                                                                                                                                                                                 |
| hdfsDirPath | HdfsDirPath | “”     | 无     | 是       | 保存到hdfs 的路径        | /test/                                                                                                                                                                                                                   |
| hdfsUrl     | HdfsUrl     | “”     | 无     | 是       | Hdfs的url                | hdfs://master:8020                                                                                                                                                                                                       |
| fileName    | FileName    | “”     | 无     | 是       | 保存到hdfs的文件名       | user.csv                                                                                                                                                                                                                 |
| delimiter   | Delimiter   | “”     | 无     | 是       | Csv文件的分隔符          | “,”                                                                                                                                                                                                                      |
| header      | Header      | “true” | 有     | 是       | Csv文件的表头            | true                                                                                                                                                                                                                     |
| neo4j_Url   | Neo4j_Url   | “”     | 无     | 是       | Neo4J的url地址           | bolt://192.168.3.141:7687                                                                                                                                                                                                |
| userName    | UserName    | “”     | 无     | 是       | Neo4j的用户名            | Neo4j                                                                                                                                                                                                                    |
| password    | Password    | “”     | 无     | 是       | Neo4j的密码              | 123456                                                                                                                                                                                                                   |
| cypher      | Cypher      | “”     | “”     | 是       | 导入csv文件的cypher语句  | LOAD CSV WITH HEADERS FROM 'http://master:50070//test/user.csv?op=OPEN' AS line FIELDTERMINATOR ',' CREATE (n:user{userid:line.id,username:line.name,userscore:line.score,userschool:line.school,userclass:line.class})  |

## 11.2 [PutNeo4](https://github.com/cas-bigdatalab/piflow/blob/master/piflow-bundle/src/main/scala/cn/piflow/bundle/neo4j/PutNeo4j.scala)

写入数据到neo4j

### 11.2.1 port

Inport：默认端口

outport：无

### 11.2.2 properties

| 名称      | 展示名称  | 默认值 | 允许值 | 是否必填 | 描述      |
|-----------|-----------|--------|--------|----------|-----------|
| Url       | Url       | “”     | 无     | 是       | Neo4j地址 |
| userName  | userName  | “”     | 无     | 是       | 用户名    |
| password  | password  | “”     | 无     | 是       | 密码      |
| labelName | labelName | “”     | 无     | 是       | 表名      |

## 11.3 [RunCypher](https://github.com/cas-bigdatalab/piflow/blob/master/piflow-bundle/src/main/scala/cn/piflow/bundle/neo4j/RunCypher.scala)

执行Cypher语句

### 11.3.1 port

Inport：默认端口

outport：无

### 11.3.2 properties

| 名称     | 展示名称 | 默认值 | 允许值 | 是否必填 | 描述           | 例子                                                      |
|----------|----------|--------|--------|----------|----------------|-----------------------------------------------------------|
| Url      | Url      | “”     | 无     | 是       | Neo4j的url地址 | bolt://192.168.3.141:7687                                 |
| userName | UserName | “”     | 无     | 是       | 用户名         | Neo4j                                                     |
| password | Password | “”     | 无     | 是       | 密码           | 123456                                                    |
| cql      | Cql      | “”     | 无     | 是       | Cql语句        | match(n:user) where n.userid ='11' set n.userclass =null  |

# InternetWorm

## 12.1 Spider

爬取网络数据

### 12.1.1port

inport：

outport：默认端口

### 12.1.2properties

| 名称           | 展示名称       | 默认值 | 允许值 | 是否必填 | 描述                       |
|----------------|----------------|--------|--------|----------|----------------------------|
| rootUrl        | rootUrl        | “”     | 无     | 是       | 网站域名地址               |
| fistUrl        | fistUrl        | “”     | 无     | 是       | 爬取开始的页面             |
| makeupField    | makeupField    | “”     | 无     | 是       | 数据标记字段名称（key）    |
| jumpDependence | jumpDependence | “”     | 无     | 是       | 页面跳转的依赖标签         |
| fileMap        | fileMap        | “”     | 无     | 是       | 字段名称，及对应的标签路径 |
| downPath       | downPath       | “”     | 无     | 否       | 文件下载路径               |

# JDBC

## 13.1 MysqlRead

Jdbc读取mysql数据

### 13.1.1port

inport：默认端口

outport：默认端口

### 13.1.2properties

| 名称     | 展示名称 | 默认值 | 允许值 | 是否必填 | 描述                | 例子                                    |
|----------|----------|--------|--------|----------|---------------------|-----------------------------------------|
| url      | Url      | “”     | 无     | 是       | 连接mysql的Url地址  | jdbc:mysql://192.168.3.141:3306/test_db |
| user     | User     | “”     | 无     | 是       | 连接mysql的用户     | root                                    |
| password | Password | “”     | 无     | 是       | 连接mysql的用户密码 | 123456                                  |
| sql      | Sql      | “”     | 无     | 是       | 查询的sql语句       | Select \* from user                     |

## 13.2 MysqlReadIncremental

Jdbc读取mysql数据

### 13.2.1port

inport：默认端口

outport：默认端口

### 13.2.2properties

| 名称             | 展示名称         | 默认值 | 允许值 | 是否必填 | 描述                | 例子                                    |
|------------------|------------------|--------|--------|----------|---------------------|-----------------------------------------|
| url              | Url              | “”     | 无     | 是       | 连接mysql的Url地址  | jdbc:mysql://192.168.3.141:3306/test_db |
| user             | User             | “”     | 无     | 是       | 连接mysql的用户     | root                                    |
| password         | Password         | “”     | 无     | 是       | 连接mysql的用户密码 | 123456                                  |
| sql              | Sql              | “”     | 无     | 是       | 查询的sql语句       | Select \* from user                     |
| incrementalField | IncrementalField | “”     | 无     | 是       | 增加的列的名字      | update_date                             |
| incrementalStart | IncrementalStart | “”     | 无     | 是       | 增加的列起始值      | 2020-04-08                              |

## 13.3 jdbcReadFromOracle

读取oracle数据

### 13.3.1port

inport：

outport：默认端口

### 13.3.2properties

| 名称     | 展示名称 | 默认值 | 允许值 | 是否必填 | 描述                   | 例子 |
|----------|----------|--------|--------|----------|------------------------|------|
| url      | url      | “”     | 无     | 是       | 连接地址               |      |
| user     | user     | “”     | 无     | 是       | 用户                   |      |
| password | password | “”     | 无     | 是       | 密码                   |      |
| sql      | sql      | “”     | 无     | 是       | 查询的sql语句          |      |
| schame   | schame   | “”     | 无     | 是       | 查询结果的字段描述信息 |      |

## 13.4 MysqlWrite

Jdbc写入mysql数据库

### 13.4.1 port

inport：默认端口

outport：默认端口

### 13.4.2 properties

| 名称     | 展示名称 | 默认值 | 允许值 | 是否必填 | 描述                | 例子                                    |
|----------|----------|--------|--------|----------|---------------------|-----------------------------------------|
| url      | Url      | “”     | 无     | 是       | 连接mysql的Url地址  | jdbc:mysql://192.168.3.141:3306/test_db |
| user     | User     | “”     | 无     | 是       | 连接mysql的用户     | root                                    |
| password | Password | “”     | 无     | 是       | 连接mysql的用户密码 | 123456                                  |
| table    | Table    | “”     | 无     | 是       | 表名                | test                                    |

## 13.5 OracleRead

从oracle中读取数据

### 13.5.1port

inport：默认端口

outport：默认端口

### 13.5.2properties

| 名称     | 展示名称 | 默认值 | 允许值 | 是否必填 | 描述                 | 例子                                                                                                                                                |
|----------|----------|--------|--------|----------|----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|
| url      | Url      | “”     | 无     | 是       | 连接oracle的Url地址  | jdbc:oracle:thin:@(DESCRIPTION =(ADDRESS_LIST =(ADDRESS=(PROTOCOL=TCP)(HOST=192.168.2.237)(PORT=1521)))(CONNECT_DATA=(SERVICE_NAME=RACDB_STANDBY))) |
| user     | User     | “”     | 无     | 是       | 连接oracle的用户     | oracle                                                                                                                                              |
| password | Password | “”     | 无     | 是       | 连接oracle的用户密码 | 123456                                                                                                                                              |
| sql      | Sql      | “”     | 无     | 是       | sql查询语句          | Select \* from test                                                                                                                                 |

## 13.6 OracleReadByPartition

从oracle中分区读取数据

### 13.6.1port

inport：默认端口

outport：默认端口

### 13.6.2properties

| 名称            | 展示名称        | 默认值 | 允许值 | 是否必填 | 描述                 | 例子                                                                                                                                                |
|-----------------|-----------------|--------|--------|----------|----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|
| url             | Url             | “”     | 无     | 是       | 连接oracle的Url地址  | jdbc:oracle:thin:@(DESCRIPTION =(ADDRESS_LIST =(ADDRESS=(PROTOCOL=TCP)(HOST=192.168.2.237)(PORT=1521)))(CONNECT_DATA=(SERVICE_NAME=RACDB_STANDBY))) |
| user            | User            | “”     | 无     | 是       | 连接oracle的用户     | oracle                                                                                                                                              |
| password        | Password        | “”     | 无     | 是       | 连接oracle的用户密码 | 123456                                                                                                                                              |
| sql             | Sql             | “”     | 无     | 是       | Sql查询语句          | Select \* from test                                                                                                                                 |
| partitionColumn | PartitionColumn | “”     | 无     | 否       | 分区的列             | id                                                                                                                                                  |
| lowerBound      | LowerBound      | “”     | 无     | 否       | 分区列的下限         | 1                                                                                                                                                   |
| upperBound      | UpperBound      | “”     | 无     | 否       | 分区列的上限         | 100                                                                                                                                                 |
| numPartitions   | NumPartitions   | “”     | 无     | 否       | 分区的数量           | 20                                                                                                                                                  |

## 13.7 OracleWrite

写入数据到oracle数据库

### 13.7.1port

inport：默认端口

outport：默认端口

### 13.7.2properties

| 名称     | 展示名称 | 默认值 | 允许值 | 是否必填 | 描述                 | 例子                                                                                                                                                |
|----------|----------|--------|--------|----------|----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|
| url      | Url      | “”     | 无     | 是       | 连接oracle的Url地址  | jdbc:oracle:thin:@(DESCRIPTION =(ADDRESS_LIST =(ADDRESS=(PROTOCOL=TCP)(HOST=192.168.2.237)(PORT=1521)))(CONNECT_DATA=(SERVICE_NAME=RACDB_STANDBY))) |
| user     | User     | “”     | 无     | 是       | 连接oracle的用户     | oracle                                                                                                                                              |
| password | Password | “”     | 无     | 是       | 连接oracle的用户密码 | 123456                                                                                                                                              |
| table    | Table    | “”     | 无     | 是       | 表名                 |  test                                                                                                                                               |

## 13.8 SelectImpala

查询impala数据

### 13.8.1port

inport：

outport：默认端口

### 13.8.2properties

| 名称         | 展示名称     | 默认值 | 允许值 | 是否必填 | 描述                   | 例子 |
|--------------|--------------|--------|--------|----------|------------------------|------|
| url          | Url          | “”     | 无     | 是       | Impala连接路径         |      |
| user         | User         | “”     | 无     | 否       | Impala用户             |      |
| password     | Password     | “”     | 无     | 否       | 用户密码               |      |
| sql          | Sql          | “”     | 无     | 是       | 查询的sql语句          |      |
| schameString | SchameString | “”     | 无     | 是       | 查询结果的字段描述信息 |      |

# Json

## 14.1 jsonParser

Json文件解析

### 14.1.1 port

inport：默认端口

outport：默认端口

### 14.1.2 properties

| 名称     | 展示名称 | 默认值 | 允许值 | 是否必填 | 描述                           | 例子                                           |
|----------|----------|--------|--------|----------|--------------------------------|------------------------------------------------|
| jsonPath | JsonPath | “”     | 无     | 是       | Json文件地址                   | hdfs://master:8020/work/json/test/example.json |
| tag      | Tag      | “”     | 无     | 是       | 需要解析的标签，多个以逗号分隔 | name,province_name                             |

## 14.3 FolderJsonPath

Json文件夹解析

### 14.3.1 port

inport：默认端口

outport：默认端口

### 14.3.2 properties

| 名称       | 展示名称   | 默认值 | 允许值 | 是否必填 | 描述           | 例子                                                                                     |
|------------|------------|--------|--------|----------|----------------|------------------------------------------------------------------------------------------|
| folderPath | FolderPath | “”     | 无     | 是       | 文件夹地址     | hdfs://master:8020/work/json/test/                                                       |
| tag        | Tag        | “”     | 无     | 是       | 需要解析的标签 | name,province_name，如果要打开数组字段，必须这样写：links_name（MasterField_ChildField） |

## 14.4 JsonStringParser

Json字符串解析

### 14.4.1 port

inport：默认端口

outport：默认端口

### 14.4.2 properties

| 名称       | 展示名称   | 默认值 | 允许值 | 是否必填 | 描述       | 例子                                                                                                     |
|------------|------------|--------|--------|----------|------------|----------------------------------------------------------------------------------------------------------|
| jsonString | JsonString | “”     | 无     | 是       | Json字符串 | {\\"id\\":\\"13\\",\\"name\\":\\"13\\",\\"score\\":\\"13\\",\\"school\\":\\"13\\",\\"class\\":\\"13\\"}  |

## 14.5 JsonSave

保存为Json文件

### 14.5.1 port

inport：默认端口

outport：默认端口

### 14.5.2 properties

| 名称         | 展示名称     | 默认值 | 允许值 | 是否必填 | 描述             | 例子                                   |
|--------------|--------------|--------|--------|----------|------------------|----------------------------------------|
| jsonSavePath | JsonSavePath | “”     | 无     | 是       | Json文件保存地址 | hdfs://master:8020/work/testJson/test/ |

# Message Queue

## 15.1 ReadFromKafka

从kafka读数据

### 15.1.1 port

Inport：NonePort

outport：默认端口

### 15.1.2 properties

| 名称        | 展示名称  | 默认值 | 允许值 | 是否必填 | 描述                  |
|-------------|-----------|--------|--------|----------|-----------------------|
| kafka\_host | KAFKA_STR | “”     | 无     | 是       | Kafka地址             |
| topic       | TOPIC     |        | 无     | 是       | 读取主题              |
| schema      | SCHEMA    |        | 无     | 是       | 生成DataFrame的schema |

## 15.2 WriteToKafka

向kafka写数据

### 15.2.1 port

Inport：默认端口

outport：NonePort

### 15.2.2 properties

| 名称        | 展示名称  | 默认值 | 允许值 | 是否必填 | 描述      |
|-------------|-----------|--------|--------|----------|-----------|
| kafka\_host | KAFKA_STR | “”     | 无     | 是       | Kafka地址 |
| topic       | TOPIC     |        | 无     | 是       | 写入主题  |

# Memcache

## 16.1 PutMemcache

写入memcache

### 16.1.1port

inport：默认端口

outport：

### 16.1.2properties

| 名称             | 展示名称         | 默认值 | 允许值 | 是否必填 | 描述               |
|------------------|------------------|--------|--------|----------|--------------------|
| servers          | servers          | “”     | 无     | 是       | Memcache的服务地址 |
| keyFile          | keyFile          | “”     | 无     | 是       | 作为key字段的名称  |
| weights          | weights          | “”     | 无     | 否       |                    |
| maxIdle          | maxIdle          | “”     | 无     | 否       | 最大处理时间       |
| maintSleep       | maintSleep       | “”     | 无     | 否       | 主线程睡眠时间     |
| nagle            | nagle            | “”     | 无     | 否       | TCP参数            |
| socketTO         | socketTO         | “”     | 无     | 否       | 连接超时时间       |
| socketConnectTO  | socketConnectTO  | “”     | 无     | 否       | 连接次数           |

## 16.2 GetMemcache

读取memcache

### 16.2.1port

inport：默认端口

outport：默认端口

### 16.2.2properties

| 名称             | 展示名称         | 默认值 | 允许值 | 是否必填 | 描述               |
|------------------|------------------|--------|--------|----------|--------------------|
| servers          | servers          | “”     | 无     | 是       | Memcache的服务地址 |
| keyFile          | keyFile          | “”     | 无     | 是       | 作为key字段的名称  |
| weights          | weights          | “”     | 无     | 否       |                    |
| maxIdle          | maxIdle          | “”     | 无     | 否       | 最大处理时间       |
| maintSleep       | maintSleep       | “”     | 无     | 否       | 主线程睡眠时间     |
| nagle            | nagle            | “”     | 无     | 否       | TCP参数            |
| socketTO         | socketTO         | “”     | 无     | 否       | 连接超时时间       |
| socketConnectTO  | socketConnectTO  | “”     | 无     | 否       | 连接次数           |
| schame           | schame           | “”     | 无     | 是       | 字段描述细信息     |

## 16.3 ComplementByMemcache

读取memcache，补充原表

### 16.3.1port

inport：默认端口

outport：默认端口

### 16.3.2properties

| 名称             | 展示名称         | 默认值 | 允许值 | 是否必填 | 描述               |
|------------------|------------------|--------|--------|----------|--------------------|
| servers          | servers          | “”     | 无     | 是       | Memcache的服务地址 |
| keyFile          | keyFile          | “”     | 无     | 是       | 作为key字段的名称  |
| weights          | weights          | “”     | 无     | 否       |                    |
| maxIdle          | maxIdle          | “”     | 无     | 否       | 最大处理时间       |
| maintSleep       | maintSleep       | “”     | 无     | 否       | 主线程睡眠时间     |
| nagle            | nagle            | “”     | 无     | 否       | TCP参数            |
| socketTO         | socketTO         | “”     | 无     | 否       | 连接超时时间       |
| socketConnectTO  | socketConnectTO  | “”     | 无     | 否       | 连接次数           |
| replaceField     | replaceField     | “”     | 无     | 是       | 你希望补充的字段   |

# Microorganism

## 17.1 BioprojectData

>   解析Bioproject数据

### 17.1.1 Port

>   inport：默认端口

>   outport：默认端口

### 17.1.2 properties

| **名称**  | **展示名称** | **默认值** | **允许值** | **是否必填** | **描述** |
|-----------|--------------|------------|------------|--------------|----------|
| cachePath | cachePath    | “”         |            | 是           | 缓存路径 |

## 17.2 BioSample

>   解析biosample数据

### 17.2.1 Port

>   inport：默认端口

>   outport：默认端口

### 17.2.2 properties

| **名称**  | **展示名称** | **默认值** | **允许值** | **是否必填** | **描述** |
|-----------|--------------|------------|------------|--------------|----------|
| cachePath | cachePath    | “”         |            | 是           | 缓存路径 |

## 17.3 EmblData

>   解析embl数据

### 17.3.1 Port

>   inport：默认端口

>   outport：默认端口

### 17.3.2 properties

| **名称**  | **展示名称** | **默认值** | **允许值** | **是否必填** | **描述** |
|-----------|--------------|------------|------------|--------------|----------|
| cachePath | cachePath    | “”         |            | 是           | 缓存路径 |

## 17.4 Ensembl

>   解析Ensembl_gff3数据

### 17.4.1 Port

>   inport：默认端口

>   outport：默认端口

### 17.4.2 properties

| **名称**  | **展示名称** | **默认值** | **允许值** | **是否必填** | **描述** |
|-----------|--------------|------------|------------|--------------|----------|
| cachePath | cachePath    | “”         |            | 是           | 缓存路径 |

## 17.5 GenbankData

>   解析genbank数据

### 17.5.1 Port

>   inport：默认端口

>   outport：默认端口

### 17.5.2 properties

| **名称**  | **展示名称** | **默认值** | **允许值** | **是否必填** | **描述** |
|-----------|--------------|------------|------------|--------------|----------|
| cachePath | cachePath    | “”         |            | 是           | 缓存路径 |

## 17.6 Gene

>   解析gene数据

### 17.6.1 Port

>   inport：默认端口

>   outport：默认端口

### 17.6.2 properties

| **名称**  | **展示名称** | **默认值** | **允许值** | **是否必填** | **描述** |
|-----------|--------------|------------|------------|--------------|----------|
| cachePath | cachePath    | “”         |            | 是           | 缓存路径 |

## 17.7 GoData

>   解析go数据

### 17.7.1 Port

>   inport：默认端口

>   outport：默认端口

### 17.7.2 properties

| **名称**  | **展示名称** | **默认值** | **允许值** | **是否必填** | **描述** |
|-----------|--------------|------------|------------|--------------|----------|
| cachePath | cachePath    | “”         |            | 是           | 缓存路径 |

## 17.8 GoldData

>   解析golddata数据

### 17.8.1 Port

>   inport：默认端口

>   outport：默认端口

### 17.8.2 properties

| **名称**  | **展示名称** | **默认值** | **允许值** | **是否必填** | **描述** |
|-----------|--------------|------------|------------|--------------|----------|
| cachePath | cachePath    | “”         |            | 是           | 缓存路径 |

## 17.9 InterproData

>   解析interpro数据

### 17.9.1 Port

>   inport：默认端口

>   outport：默认端口

### 17.9.2 properties

| **名称**  | **展示名称** | **默认值** | **允许值** | **是否必填** | **描述** |
|-----------|--------------|------------|------------|--------------|----------|
| cachePath | cachePath    | “”         |            | 是           | 缓存路径 |

## 17.10. MicrobeGEnomeData

>   解析 MicrobeGEnome数据

### 17.10.1 Port

>   inport：默认端口

>   outport：默认端口

### 17.10.2 properties

| **名称**  | **展示名称** | **默认值** | **允许值** | **是否必填** | **描述** |
|-----------|--------------|------------|------------|--------------|----------|
| cachePath | cachePath    | “”         |            | 是           | 缓存路径 |

## 17.11 PDBData

>   解析 pdb数据

### 17.11.1 Port

>   inport：默认端口

>   outport：默认端口

### 17.11.2 properties

| **名称**  | **展示名称** | **默认值** | **允许值** | **是否必填** | **描述** |
|-----------|--------------|------------|------------|--------------|----------|
| cachePath | cachePath    | “”         |            | 是           | 缓存路径 |

## 17.12 PfamData

>   解析 pfam数据

### 17.12.1 Port

>   inport：默认端口

>   outport：默认端口

### 17.12.2 properties

| **名称**  | **展示名称** | **默认值** | **允许值** | **是否必填** | **描述** |
|-----------|--------------|------------|------------|--------------|----------|
| cachePath | cachePath    | “”         |            | 是           | 缓存路径 |

## 17.13 RefseqData

>   解析 refSeq数据

### 17.13.1 Port

>   inport：默认端口

>   outport：默认端口

### 17.13.2 properties

| **名称**  | **展示名称** | **默认值** | **允许值** | **是否必填** | **描述** |
|-----------|--------------|------------|------------|--------------|----------|
| cachePath | cachePath    | “”         |            | 是           | 缓存路径 |

## 17.14 SwissprotData

>   解析 swiss数据

### 17.14.1 Port

>   inport：默认端口

>   outport：默认端口

### 17.14.2 properties

| **名称**  | **展示名称** | **默认值** | **允许值** | **是否必填** | **描述** |
|-----------|--------------|------------|------------|--------------|----------|
| cachePath | cachePath    | “”         |            | 是           | 缓存路径 |

## 17.15 TaxonomyData

>   解析 TaxonomyParse数据

### 17.15.1 Port

>   inport：默认端口

>   outport：默认端口

### 17.15.2 properties

| **名称**  | **展示名称** | **默认值** | **允许值** | **是否必填** | **描述** |
|-----------|--------------|------------|------------|--------------|----------|
| cachePath | cachePath    | “”         |            | 是           | 缓存路径 |

## 17.16 Pathway

>   解析 KeggPathwayParse数据

### 17.16.1 Port

>   inport：默认端口

>   outport：默认端口

### 17.16.2 properties

| **名称**  | **展示名称** | **默认值** | **允许值** | **是否必填** | **描述** |
|-----------|--------------|------------|------------|--------------|----------|
| cachePath | cachePath    | “”         |            | 是           | 缓存路径 |

## 17.17 MedlineData

>   解析 TaxonomyParse数据

### 17.17.1 Port

>   inport：默认端口

>   outport：默认端口

### 17.17.2 properties

| **名称**  | **展示名称** | **默认值** | **允许值** | **是否必填** | **描述** |
|-----------|--------------|------------|------------|--------------|----------|
| cachePath | cachePath    | “”         |            | 是           | 缓存路径 |

# MechineLearning Classification

## 18.1DecisionTreeTraining

决策树分类模型训练

### 18.1.1 port

Inport：NonePort

outport：默认端口

### 18.1.2 properties

| 名称                | 展示名称              | 默认值 | 允许值 | 是否必填 | 描述                             |
|---------------------|-----------------------|--------|--------|----------|----------------------------------|
| training\_data_path | TRAINING_DATA_PATH    | “”     | 无     | 是       | 训练数据路径                     |
| model\_save_path    | MODEL_SAVE_PATH       |        | 无     | 是       | 模型保存路径                     |
| maxBins             | MAX_BINS              |        | 无     | 是       | 连续属性分裂最大数目             |
| maxDepth            | MAX_DEPTH             |        | 无     | 是       | 树的最大深度                     |
| minInfoGain         | MIN_INFO\_GAIN        |        | 无     | 是       | 能作为分裂属性的最小信息增益     |
| minInstancePerNode  | MIN_INSTANCE_PER_NODE |        | 无     | 是       | 每个节点的最小节点数目           |
| impurity            | IMPURITY              |        | 无     | 是       | 分裂准则，如信息增益或者基尼系数 |

## 18.2 DecisionTreePrediction

决策树分类预测

### 18.2.1 port

Inport：默认端口

outport：NonePort

### 18.2.2 properties

| 名称           | 展示名称       | 默认值 | 允许值 | 是否必填 | 描述         |
|----------------|----------------|--------|--------|----------|--------------|
| test_data_path | TEST_DATA_PATH | “”     | 无     | 是       | 测试数据路径 |
| model_path     | MODEL_PATH     |        | 无     | 是       | 模型加载路径 |

## 18.3 GBTTraining

GBT模型训练

### 18.3.1 port

Inport：NonePort

outport：默认端口

### 18.3.2 properties

| 名称                | 展示名称              | 默认值 | 允许值 | 是否必填 | 描述                             |
|---------------------|-----------------------|--------|--------|----------|----------------------------------|
| training\_data_path | TRAINING_DATA_PATH    | “”     | 无     | 是       | 训练数据路径                     |
| model\_save_path    | MODEL_SAVE_PATH       |        | 无     | 是       | 模型保存路径                     |
| maxBins             | MAX_BINS              |        | 无     | 否       | 连续属性分裂最大数目             |
| maxDepth            | MAX_DEPTH             |        | 无     | 否       | 树的最大深度                     |
| minInfoGain         | MIN_INFO\_GAIN        |        | 无     | 否       | 能作为分裂属性的最小信息增益     |
| minInstancePerNode  | MIN_INSTANCE_PER_NODE |        | 无     | 否       | 每个节点的最小节点数目           |
| impurity            | IMPURITY              |        | 无     | 否       | 分裂准则，如信息增益或者基尼系数 |
| subSamplingRate     | SUB_SAMPLING_RATE     |        | 无     | 否       | 每棵子树的数据采样率             |
| lossType            | LOSS_TYPE             |        | 无     | 否       | 损失函数                         |
| stepSize            | STEP_SIZE             |        | 无     | 否       | 步长（学习率）                   |

## 18.4 GBTPrediction

GBT预测

### 18.4.1 port

Inport：默认端口

outport：NonePort

### 18.4.2 properties

| 名称           | 展示名称       | 默认值 | 允许值 | 是否必填 | 描述         |
|----------------|----------------|--------|--------|----------|--------------|
| test_data_path | TEST_DATA_PATH | “”     | 无     | 是       | 测试数据路径 |
| model_path     | MODEL_PATH     |        | 无     | 是       | 模型加载路径 |

## 18.5LogisticRegressionTraining

LogisticRegression模型训练

### 18.5.1 port

Inport：NonePort

outport：默认端口

### 18.5.2 properties

| 名称                | 展示名称           | 默认值 | 允许值 | 是否必填 | 描述         |
|---------------------|--------------------|--------|--------|----------|--------------|
| training\_data_path | TRAINING_DATA_PATH | “”     | 无     | 是       | 训练数据路径 |
| model\_save_path    | MODEL_SAVE_PATH    |        | 无     | 是       | 模型保存路径 |
| maxIter             | MAX_ITER           |        | 无     | 否       | 最大迭代次数 |
| minTol              | MIN_TOL            |        | 无     | 否       | 迭代收敛容差 |
| regParam            | REG_PARAM          |        | 无     | 否       | 正则化       |
| elasticNetParam     | ELASTIC_NET_PARAM  |        | 无     | 否       |              |
| threshold           | THRESHOLD          |        | 无     | 否       | 分类         |
| family              | FAMILY             |        |        |          |              |

## 18.6 LogisticRegressionPrediction

LogisticRegression分类预测

### 18.6.1 port

Inport：默认端口

outport：NonePort

### 18.6.2 properties

| 名称           | 展示名称       | 默认值 | 允许值 | 是否必填 | 描述         |
|----------------|----------------|--------|--------|----------|--------------|
| test_data_path | TEST_DATA_PATH | “”     | 无     | 是       | 测试数据路径 |
| model_path     | MODEL_PATH     |        | 无     | 是       | 模型加载路径 |

## 18.7MultilayerPerceptronTraining

多层神经网络模型训练

### 18.7.1 port

Inport：NonePort

outport：默认端口

### 18.7.2 properties

| 名称                | 展示名称           | 默认值 | 允许值 | 是否必填 | 描述               |
|---------------------|--------------------|--------|--------|----------|--------------------|
| training\_data_path | TRAINING_DATA_PATH | “”     | 无     | 是       | 训练数据路径       |
| model\_save_path    | MODEL_SAVE_PATH    |        | 无     | 是       | 模型保存路径       |
| maxIter             | MAX_ITER           |        | 无     | 否       | 最大迭代次数       |
| minTol              | MIN_TOL            |        | 无     | 否       | 迭代收敛容差       |
| layers              | LAYERS             |        | 无     | 是       | 输出层和输入层层数 |
| threshold           | THRESHOLD          |        | 无     | 是       | 分类概率数组       |
| stepSize            | STEP_SIZE          |        | 无     | 否       | 步长（学习率）     |

## 18.8 MultilayerPerceptronPrediction

多层神经网络分类预测

### 18.8.1 port

Inport：默认端口

outport：NonePort

### 18.8.2 properties

| 名称           | 展示名称       | 默认值 | 允许值 | 是否必填 | 描述         |
|----------------|----------------|--------|--------|----------|--------------|
| test_data_path | TEST_DATA_PATH | “”     | 无     | 是       | 测试数据路径 |
| model_path     | MODEL_PATH     |        | 无     | 是       | 模型加载路径 |

## 18.9NavieBayesTraining

朴素贝叶斯模型训练

### 18.9.1 port

Inport：NonePort

outport：默认端口

### 18.9.2 properties

| 名称                | 展示名称           | 默认值 | 允许值 | 是否必填 | 描述         |
|---------------------|--------------------|--------|--------|----------|--------------|
| training\_data_path | TRAINING_DATA_PATH | “”     | 无     | 是       | 训练数据路径 |
| model\_save_path    | MODEL_SAVE_PATH    |        | 无     | 是       | 模型保存路径 |
| smooth_value        | SMOOTH_VALUE       |        | 无     | 否       | 平滑因子     |

## 18.10 NavieBayesPrediction

决策树分类预测

### 18.10.1 port

Inport：默认端口

outport：NonePort

### 18.10.2 properties

| 名称           | 展示名称       | 默认值 | 允许值 | 是否必填 | 描述         |
|----------------|----------------|--------|--------|----------|--------------|
| test_data_path | TEST_DATA_PATH | “”     | 无     | 是       | 测试数据路径 |
| model_path     | MODEL_PATH     |        | 无     | 是       | 模型加载路径 |

## 18.11RandomForestTraining

随机森林分类模型训练

### 18.11.1 port

Inport：NonePort

outport：默认端口

### 18.11.2 properties

| 名称                  | 展示名称                | 默认值 | 允许值 | 是否必填 | 描述                             |
|-----------------------|-------------------------|--------|--------|----------|----------------------------------|
| training\_data_path   | TRAINING_DATA_PATH      | “”     | 无     | 是       | 训练数据路径                     |
| model\_save_path      | MODEL_SAVE_PATH         |        | 无     | 是       | 模型保存路径                     |
| maxBins               | MAX_BINS                |        | 无     | 否       | 连续属性分裂最大数目             |
| maxDepth              | MAX_DEPTH               |        | 无     | 否       | 树的最大深度                     |
| minInfoGain           | MIN_INFO\_GAIN          |        | 无     | 否       | 能作为分裂属性的最小信息增益     |
| minInstancePerNode    | MIN_INSTANCE_PER_NODE   |        | 无     | 否       | 每个节点的最小节点数目           |
| impurity              | IMPURITY                |        | 无     | 否       | 分裂准则，如信息增益或者基尼系数 |
| subSamplingRate       | SUB_SAMPLING_RATE       |        | 无     | 否       | 每棵子树的数据采样率             |
| featureSubsetStrategy | FEATURE_SUBSET_STRATEGY |        | 无     | 否       | 属性选择策略                     |
| numTrees              | NUM_TREES               |        | 无     | 否       | 训练子树数目                     |

## 18.12 RandomForestPrediction

随机森林分类预测

### 18.12.1 port

Inport：默认端口

outport：NonePort

### 18.12.2 properties

| 名称           | 展示名称       | 默认值 | 允许值 | 是否必填 | 描述         |
|----------------|----------------|--------|--------|----------|--------------|
| test_data_path | TEST_DATA_PATH | “”     | 无     | 是       | 测试数据路径 |
| model_path     | MODEL_PATH     |        | 无     | 是       | 模型加载路径 |

# MechineLearning Clustering

## 19.1BisetingKmeansTraining

BisetingKmeans模型训练

### 19.1.1 port

Inport：NonePort

outport：默认端口

### 19.1.2 properties

| 名称                | 展示名称           | 默认值 | 允许值 | 是否必填 | 描述         |
|---------------------|--------------------|--------|--------|----------|--------------|
| training\_data_path | TRAINING_DATA_PATH | “”     | 无     | 是       | 训练数据路径 |
| model\_save_path    | MODEL_SAVE_PATH    |        | 无     | 是       | 模型保存路径 |
| maxIters            | MAX_ITERS          |        | 无     | 否       | 最大迭代次数 |
| k                   | K                  |        | 无     | 是       | 聚类簇数目   |

## 19.2 BisetingKmeansPrediction

BisetingKmeans预测

### 19.2.1 port

Inport：默认端口

outport：NonePort

### 19.2.2 properties

| 名称           | 展示名称       | 默认值 | 允许值 | 是否必填 | 描述         |
|----------------|----------------|--------|--------|----------|--------------|
| test_data_path | TEST_DATA_PATH | “”     | 无     | 是       | 测试数据路径 |
| model_path     | MODEL_PATH     |        | 无     | 是       | 模型加载路径 |

## 19.3GaussianMixtureTraining

混合高斯模型训练

### 19.3.1 port

Inport：NonePort

outport：默认端口

### 19.3.2 properties

| 名称                | 展示名称           | 默认值 | 允许值 | 是否必填 | 描述         |
|---------------------|--------------------|--------|--------|----------|--------------|
| training\_data_path | TRAINING_DATA_PATH | “”     | 无     | 是       | 训练数据路径 |
| model\_save_path    | MODEL_SAVE_PATH    |        | 无     | 是       | 模型保存路径 |
| maxIters            | MAX_ITERS          |        | 无     | 否       | 最大迭代次数 |
| k                   | K                  |        | 无     | 是       | 聚类簇数目   |
| tol                 | TOL                |        | 无     | 否       | 迭代收敛误差 |

## 19.4 GaussianMixturePrediction

混合高斯预测

### 19.4.1 port

Inport：默认端口

outport：NonePort

### 19.4.2 properties

| 名称           | 展示名称       | 默认值 | 允许值 | 是否必填 | 描述         |
|----------------|----------------|--------|--------|----------|--------------|
| test_data_path | TEST_DATA_PATH | “”     | 无     | 是       | 测试数据路径 |
| model_path     | MODEL_PATH     |        | 无     | 是       | 模型加载路径 |

## 19.5KmeansTraining

Kmeans模型训练

### 19.5.1 port

Inport：NonePort

outport：默认端口

### 19.5.2 properties

| 名称                | 展示名称           | 默认值 | 允许值 | 是否必填 | 描述         |
|---------------------|--------------------|--------|--------|----------|--------------|
| training\_data_path | TRAINING_DATA_PATH | “”     | 无     | 是       | 训练数据路径 |
| model\_save_path    | MODEL_SAVE_PATH    |        | 无     | 是       | 模型保存路径 |
| maxIters            | MAX_ITERS          |        | 无     | 否       | 最大迭代次数 |
| k                   | K                  |        | 无     | 是       | 聚类簇数目   |
| minTol              | MIN_TOL            |        | 无     | 否       | 迭代收敛误差 |

## 19.6 KmeansPrediction

Kmeans聚类预测

### 19.6.1 port

Inport：默认端口

outport：NonePort

### 19.6.2 properties

| 名称           | 展示名称       | 默认值 | 允许值 | 是否必填 | 描述         |
|----------------|----------------|--------|--------|----------|--------------|
| test_data_path | TEST_DATA_PATH | “”     | 无     | 是       | 测试数据路径 |
| model_path     | MODEL_PATH     |        | 无     | 是       | 模型加载路径 |

## 19.7LDATraining

LDA主题模型训练

### 19.7.1 port

Inport：NonePort

outport：默认端口

### 19.7.2 properties

| 名称                | 展示名称             | 默认值 | 允许值 | 是否必填 | 描述         |
|---------------------|----------------------|--------|--------|----------|--------------|
| training\_data_path | TRAINING_DATA_PATH   | “”     | 无     | 是       | 训练数据路径 |
| model\_save_path    | MODEL_SAVE_PATH      |        | 无     | 是       | 模型保存路径 |
| maxIters            | MAX_ITERS            |        | 无     | 否       | 最大迭代次数 |
| k                   | K                    |        | 无     | 是       | 聚类簇数目   |
| docConcertration    | DOC_CONCERTRATION    |        | 无     | 否       |              |
| topiccConcertration | TOPIC_CCONCERTRATION |        | 无     | 否       |              |
| checkpointInterval  | CHECKPOINT_INTERVAL  |        | 无     | 是       |              |
| optimizer           | OPTIMIZER            |        | 无     | 否       |              |

## 19.8 LDAPrediction

LDA聚类预测

### 19.8.1 port

Inport：默认端口

outport：NonePort

### 19.8.2 properties

| 名称           | 展示名称       | 默认值 | 允许值 | 是否必填 | 描述         |
|----------------|----------------|--------|--------|----------|--------------|
| test_data_path | TEST_DATA_PATH | “”     | 无     | 是       | 测试数据路径 |
| model_path     | MODEL_PATH     |        | 无     | 是       | 模型加载路径 |

# MechineLearning Feature

## 20.1 WordToVec

WordToVec文本向量生成

### 20.1.1 port

Inport：默认

outport：默认端口

### 20.2.2 properties

| 名称              | 展示名称            | 默认值 | 允许值 | 是否必填 | 描述                        |
|-------------------|---------------------|--------|--------|----------|-----------------------------|
| colName           | COL_NAME            | “”     | 无     | 是       | 要处理的字段名              |
| outputCol         | OUTPUT_COL          |        | 无     | 是       | 输出DataFrame文本向量字段名 |
| maxIter           | MAX_ITER            |        | 无     | 否       | 最大迭代次数                |
| maxSentenceLength | MAX_SENTENCE_LENGTH |        | 无     | 否       | 单个句子的最大长度          |
| minCount          | MIN\_COUNT          |        | 无     | 否       | 最小词频                    |
| numPartitions     | NUM_PARTITIONS      |        | 无     | 否       |                             |
| stepSize          | STEP_SIZE           |        | 无     | 否       | 步长（学习率）              |
| vectorSize        | VECTOR_SIZE         |        | 无     | 否       | 文本向量纬度数目            |

# MongoDB

## 21.1 GetMomgo

读取mongo

### 21.1.1port

inport：

outport：默认端口

### 21.1.2properties

| 名称        | 展示名称    | 默认值 | 允许值 | 是否必填 | 描述          |
|-------------|-------------|--------|--------|----------|---------------|
| addresses   | addresses   | “”     | 无     | 是       | Mongo地址     |
| credentials | credentials | “”     | 无     | 否       | 连接池信息    |
| dataBase    | dataBase    | “”     | 无     | 是       | 数据库        |
| collection  | collection  | “”     | 无     | 是       | 表名          |
| sql         | sql         | “”     | 无     | 否       | 查询的sql语句 |

## 21.2 PutMomgo

写入mongo

### 21.2.1port

inport：默认端口

outport：

### 21.2.2properties

| 名称        | 展示名称    | 默认值 | 允许值 | 是否必填 | 描述       |
|-------------|-------------|--------|--------|----------|------------|
| addresses   | addresses   | “”     | 无     | 是       | Mongo地址  |
| credentials | credentials | “”     | 无     | 否       | 连接池信息 |
| dataBase    | dataBase    | “”     | 无     | 是       | 数据库     |
| collection  | collection  | “”     | 无     | 是       | 表名       |

# RDF

## 22.1 RDF2DF

将数据分流

###  port

inport：默认端口

outport：任意端口

###  properties

| 名称     | 展示名称        | 默认值                           | 允许值 | 是否必填 | 描述                                                                                                                                                                                                                                                                                                                                 |
|----------|-----------------|----------------------------------|--------|----------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| fileName | file name       | default                          | 无     | 否       | File containing all arguments, used as an alternative to supplying all arguments on the command line directly.Each argument can be on a separate line or multiple arguments per line separated by space.Arguments containing spaces needs to be quoted.Supplying other arguments in addition to this file argument is not supported. |
| storeDir | store directory | /data/neo4j-db/database/graph.db | 无     | 是       | Database directory to import into. Must not contain existing database.                                                                                                                                                                                                                                                               |

## CsvToNeo4J

this stop use linux shell & neo4j-import command to lead CSV file data
create/into a database**. T**he neo4j version is 3.0+"

### 22.2.1 port

inport：无端口

outport：无端口

### 22.2.2 properties

| 名称               | 展示名称              | 默认值                                                                                                                                                                                                                                                                                                       | 允许值     | 是否必填 | 描述                                                                                                                                                                                                 |
|--------------------|-----------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------|----------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| filePath           | inputHDFSFilePath     | “”                                                                                                                                                                                                                                                                                                           | 无         | 是       | The path of the input rdf file                                                                                                                                                                       |
| filePath           | isFromFront           | FALSE                                                                                                                                                                                                                                                                                                        | true,false | 是       | identify the file path source(should have same schema)                                                                                                                                               |
| propertyRegex      | property regex        | \<(?\<prefix\>http:\\\\/\\\\/[\^\>]+\\\\/)(?\<id\>[\^\\\\/][-A-Za-z0-9._\#\$%\^&\*!@\~]+)\> \<(?\<pprefix\>http:\\\\/\\\\/[\^\>]+\\\\/)(?\<name\>[\^\\\\/][-A-Za-z0-9._\#\$%\^&\*!@\~]+)\> \\"(?\<value\>.+)\\" \\\\.                                                                                        | 无         | 是       | define the propertyRegex to parse the n3 file's property line "this regex string should be fully named and regula "you need to SPECIFIC five value's name "1.prefix 2.id 3.pprefix 4.name 5.value" + |
| relationshipRegex  | relationship regex    | \<(?\<prefix1\>http:\\\\/\\\\/[\^\>]+\\\\/)(?\<id1\>[\^\\\\/][-A-Za-z0-9._\#\$%\^&\*!@\~]+)\> \<(?\<tprefix\>http:\\\\/\\\\/[\^\>]+\\\\/)(?\<type\>[\^\\\\/][-A-Za-z0-9._\#\$%\^&\*!@\~]+)(?\<!\#type)\> \<(?\<prefix2\>http:\\\\/\\\\/[\^\>]+\\\\/)(?\<id2\>[\^\\\\/][-A-Za-z0-9._\#\$%\^&\*!@\~]+)\> \\\\. | 无         | 是       |  "the form should be like this : "(?\<prefix\>...?\<id\>... ?\<pprefix\>...?\<name\> ?\<value\>... "check the default value carefully to knowledge the right structure                               |
| entityRegex        | entity regex          | (\<(?\<prefix\>http:\\\\/\\\\/[\^\>]+\\\\/)(?\<id\>[\^\\\\/][-A-Za-z0-9._\#\$%\^&\*!@\~]+)\> \<(?:http:\\\\/\\\\/[\^\>]+\\\\/)(?:[\^\\\\/][-A-Za-z0-9._\#\$%\^&\*!@\~]+)(?:\#type)\> \<(?\<lprefix\>http:\\\\/\\\\/[\^\>]+\\\\/)(?\<label\>[\^\\\\/][-A-Za-z0-9._\#\$%\^&\*!@\~]+)\> \\\\.                   | 无         | 是       |  "the form should be like this : "(?\<prefix1\>...?\<id1\>... ?\<tprefix\>...?\<type\> ?\<prefix2\>...?\<id2\> "check the default value carefully to knowledge the right structure                   |
| relationshipSchema | relationship's schema | ENTITY_ID:START_ID,role,ENTITY_ID:END_ID,RELATION_TYPE:TYPE                                                                                                                                                                                                                                                  | 无         | 是       |  "the form should be like this : "(?\<prefix\>...?\<id\>... ... ?\<lprefix\>...?\<label\> "check the default value carefully to knowledge the right structure                                        |
| entityIdName       | entity's id           | ENTITY_ID:ID                                                                                                                                                                                                                                                                                                 | 无         | 是       | define the id of entity, as a user, "you should ponder the style like \\'id\\' + :I "make sure your schema looks like the default value                                                              |
| entityLabelName    | entity's label        | ENTITY_TYPE:LABEL                                                                                                                                                                                                                                                                                            | 无         | 是       | define the label of entity, as a user, "you should ponder the style like \\'label\\' + :LABE "make sure your schema looks like the default value                                                     |

# Redis

## 23.1 ReadFromRedis

从Redis读数据

### 23.1.1 port

Inport：默认端口

outport：默认端口

### 23.1.2 properties

| 名称        | 展示名称    | 默认值 | 允许值 | 是否必填 | 描述                       | 例子   |
|-------------|-------------|--------|--------|----------|----------------------------|--------|
| redis_host  | Redis_Host  | “”     | 无     | 是       | Redis地址                  | master |
| Port        | Port        |        |        | 是       | 连接redis的端口号          | 7000   |
| password    | Password    |        | 无     | 是       | 连接redis的密码            | 123456 |
| schema      | Schema      |        | 无     | 是       | 要基于key从redis获取的字段 | age    |
| Column_name | Column_Name |        |        | 是       | 此列是从redis获取数据的key | id     |

## 23.2 WriteToRedis

向redis写数据

### 23.2.1 port

Inport：默认端口

outport：默认端口

### 23.2.2 properties

| 名称        | 展示名称    | 默认值 | 允许值 | 是否必填 | 描述                            | 例子   |
|-------------|-------------|--------|--------|----------|---------------------------------|--------|
| redis_host  | Redis_Host  | “”     | 无     | 是       | Redis地址                       | master |
| port        | Port        |        |        | 是       | 连接reids的端口号               | 7000   |
| password    | Password    |        | 无     | 是       | Redis的密码                     | 123456 |
| Column_Name | Column_Name |        |        | 是       | Schema中用作key的字段，必须唯一 | id     |

# Script

### 24.1.1port

inport： 默认端口

outport：默认端口

## 24.1 ExecutorShell

执行shell脚本

### 24.1.2properties

| 名称        | 展示名称    | 默认值 | 允许值 | 是否必填 | 描述                            | 例子                                           |
|-------------|-------------|--------|--------|----------|---------------------------------|------------------------------------------------|
| IP          | IP          | “”     | 无     | 是       | 本地文件所在的服务器IP          | 127.0.0.1                                      |
| User        | User        | “”     | 无     | 是       | 本地文件所在的服务器用户        | root                                           |
| PassWord    | PassWord    | “”     | 无     | 是       | 本地文件所在的服务器密码        | 123456                                         |
| shellString | ShellString | “”     | 无     | 是       | Shell脚本，多个脚本以\#\#\#分隔 | mkdir /work/\#\#\#cp /opt/1.29.3.tar.gz /work/ |

## 24.2 DataFrameRowParser

根据schema构造DataFrame

### 24.2.1port

inport： 默认端口

outport：默认端口

### 24.2.2properties

| 名称      | 展示名称  | 默认值 | 允许值 | 是否必填 | 描述           |
|-----------|-----------|--------|--------|----------|----------------|
| Schema    | Schema    | “”     | 无     | 是       | 数据的结构     |
| Separator | Separator | “”     | 无     | 是       | Schema的分隔符 |

## 24.3 ExecutePythonWithDataFrame

获取上游DataFrame并传递给Python脚本特定函数进行处理，并返回结果。需要集群各个节点安装python，jep。同时需要配置spark-env.sh中jep路径。具体如下所示，路径根据实际情况更改。

export
LD_LIBRARY_PATH=\$LD_LIBRARY_PATH:/usr/local/lib64/python3.6/site-packages/jep/

### 24.3.1port

inport： 默认端口

outport：默认端口

### 24.3.2properties

| 名称         | 展示名称     | 默认值 | 允许值 | 是否必填 | 描述                                                                    |
|--------------|--------------|--------|--------|----------|-------------------------------------------------------------------------|
| Script       | Script       | “”     | 无     | 是       | Python脚本                                                              |
| ExecFunction | ExecFunction | “”     | 无     | 是       | 要执行的Python函数，参数为List[dict]类型,返回值也应为类型为List[dict]。 |

Execfunction例子如下所示：

>   import sys

>   import os

>   import numpy as np

>   def listFunction(dictInfo):

>   newDict = {"name":"hello new user!", "id":11}

>   secondDict = {"name":"hello second user!", "id":12}

>   listInfo=[newDict, secondDict]

>   return dictInfo + listInfo

## 24.4 ExecutePython

仅执行Python脚本，不传递数据。需要集群各个节点安装python，jep。同时需要配置spark-env.sh中jep路径。具体如下所示，路径根据实际情况更改。

export
LD_LIBRARY_PATH=\$LD_LIBRARY_PATH:/usr/local/lib64/python3.6/site-packages/jep/

### 24.4.1port

inport： 默认端口

outport：默认端口

### 24.4.2properties

| 名称   | 展示名称 | 默认值 | 允许值 | 是否必填 | 描述       |
|--------|----------|--------|--------|----------|------------|
| Script | Script   | “”     | 无     | 是       | Python脚本 |
|        |          |        |        |          |            |

## 24.5 ExecuteScala

获取上游DataFrame进行处理，并将处理后的数据写到下游。

### 24.5.1port

inport： 默认端口

outport：默认端口

### 24.5.2properties

| 名称   | 展示名称 | 默认值 | 允许值 | 是否必填 | 描述                |
|--------|----------|--------|--------|----------|---------------------|
| Plugin | Plugin   | “”     | 无     | 是       | 生成的scala文件类名 |
| Script | Script   | “”     | 无     | 是       | Scala脚本           |

Script例子如下所示：

val df = in.read()

df.printSchema()

out.write(df)

# Solr

## 25.1 GetSolr

读取solr数据

### 25.1.1 port

inport：默认端口

outport：默认端口

### 25.1.2 properties

| 名称            | 展示名称        | 默认值 | 允许值 | 是否必填 | 描述               | 例子                                                |
|-----------------|-----------------|--------|--------|----------|--------------------|-----------------------------------------------------|
| solrURL         | solrURL         | “”     | 无     | 是       | solr地址           | http://mastet:8886/solr                             |
| SolrCollection  | SolrCollection  | “”     | 无     | 是       | Collection名称     | test                                                |
| q               | Q               | “”     | 无     | 否       | 查询字符串         | \*:\*                                               |
| start           | Qtart           | “”     | 无     | 否       | 结果返回的开始位置 | 1                                                   |
| rows            | Rows            | “”     | 无     | 否       | 返回的结果数       | 10                                                  |
| sortBy          | SortBy          | “”     | 无     | 否       | 排序的字段         | id                                                  |
| DescentOrAscend | DescentOrAscend | “”     | 无     | 否       | 升序或降序         | Ascend(升序) Descend(降序)                          |
| fl              | FL              | “”     | 无     | 否       | 指定返回字段       | id,name                                             |
| fq              | FQ              | “”     | 无     | 否       | 过滤条件           | id:[1 To 40]                                        |
| df              | DF              | “”     | 无     | 否       | 默认查询字段       | name                                                |
| indent          | Indent          | “”     | 无     | 否       | 是否缩进           | true\|on(此方式默认数据格式化,不填则显示数据在一行) |

## 25.2 PutSolr

写入Solr

### 25.2.1 port

inport：默认端口

outport：默认端口

### 25.2.2 properties

| 名称           | 展示名称       | 默认值 | 允许值 | 是否必填 | 描述           | 例子                    |
|----------------|----------------|--------|--------|----------|----------------|-------------------------|
| solrURL        | SolrURL        | “”     | 无     | 是       | solr地址       | http://mastet:8886/solr |
| SolrCollection | SolrCollection | “”     | 无     | 是       | Collection名称 | test                    |

# XML

## 26.1 XmlParser

解析xml文件

### 26.1.1 port

inport：默认端口

outport：默认端口

### 26.1.2 properties

| 名称    | 展示名称 | 默认值 | 允许值 | 是否必填 | 描述              | 例子                                 |
|---------|----------|--------|--------|----------|-------------------|--------------------------------------|
| xmlpath | Xmlpath  | “”     | 无     | 是       | Xml文件路径       | hdfs://master:8020/work/test/xml.xml |
| rowTag  | RowTag   | “”     | 无     | 是       | 解析的xml文件标签 | name                                 |

## 26.2 XmlParserColumns

解析上游数据中列中的xml数据,写入DateFrame

### 26.2.1port

inport：默认端口

outport：默认端口

### 26.2.2properties

| 名称        | 展示名称    | 默认值 | 允许值 | 是否必填 | 描述            | 例子     |
|-------------|-------------|--------|--------|----------|-----------------|----------|
| xmlColumns  | XmlColumns  | “”     | 无     | 是       | 解析包含xml的列 | test_xml |

## 26.3 XmlParserFolder

解析xml文件夹

### 26.3.1 port

inport：默认端口

outport：默认端口

### 26.3.2 properties

| 名称    | 展示名称 | 默认值 | 允许值 | 是否必填 | 描述              | 例子                              |
|---------|----------|--------|--------|----------|-------------------|-----------------------------------|
| xmlpath | Xmlpath  | “”     | 无     | 是       | Xml文件夹路径     | hdfs://master:8020/work/test/xml/ |
| rowTag  | RowTag   | “”     | 无     | 是       | 解析xml文件的标签 | id,name                           |

## 26.4 XmlStringParser

解析xml字符串

### 26.4.1port

inport：默认端口

outport：默认端口

### 26.4.2properties

| 名称      | 展示名称  | 默认值 | 允许值 | 是否必填 | 描述         | 例子                                                                                                                                                                                                                                                                                  |
|-----------|-----------|--------|--------|----------|--------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| xmlString | XmlString | “”     | 无     | 是       | Xml字符串    | \<sites\>\\n \<site\>\\n \<name\>菜鸟教程\</name\>\\n \<url\>www.runoob.com\</url\>\\n \</site\>\\n \<site\>\\n \<name\>Google\</name\>\\n \<url\>www.google.com\</url\>\\n \</site\>\\n \<site\>\\n \<name\>淘宝\</name\>\\n \<url\>www.taobao.com\</url\>\\n \</site\>\\n\</sites\> |
| label     | Label     | “”     | 无     | 是       | 标签路径     | sites,site                                                                                                                                                                                                                                                                            |
| schema    | Schema    | “”     | 无     | 是       | 解析的标签名 | name,url                                                                                                                                                                                                                                                                              |

## 26.5 XmlSave

保存xml文件

### 26.5.1port

inport：默认端口

outport：默认端口

### 26.5.2properties

| 名称        | 展示名称    | 默认值 | 允许值 | 是否必填 | 描述            | 例子                                 |
|-------------|-------------|--------|--------|----------|-----------------|--------------------------------------|
| xmlSavePath | XmlSavePath | “”     | 无     | 是       | Xml文件保存路径 | hdfs://master:8020/work/test/test.xm |

# Streaming

## 28.1 FlumeStream

获取flume的实时流数据

### 28.1.1port

inport：

outport：默认端口

### 28.1.2properties

| 名称          | 展示名称      | 默认值 | 允许值 | 是否必填 | 描述               |
|---------------|---------------|--------|--------|----------|--------------------|
| hostname      | hostname      | “”     | 无     | 是       | Avro 主机host名    |
| Port          | Port          | “”     | 无     | 是       | Avro主机端口       |
| batchDuration | batchDuration | “”     | 无     | 否       | 获取数据的时间间隔 |
|               |               |        |        |          |                    |

## 28.2 KafkaStream

获取kafka的实时流数据

### 28.2.1port

inport：

outport：默认端口

### 28.2.2properties

| 名称          | 展示名称      | 默认值 | 允许值 | 是否必填 | 描述                      |
|---------------|---------------|--------|--------|----------|---------------------------|
| Brokers       | Brokers       | “”     | 无     | 是       | Kafka brokers,以逗号分隔  |
| groupId       | Port          | “”     | 无     | 是       | Kafka consumer group      |
| Topics        | Topics        | “”     | 无     | 否       | Kafka topic名，以逗号分割 |
| batchDuration | batchDuration | “”     | 无     | 否       | 获取数据的时间间隔        |

## 28.3 SocketTextStream

获取sokcet的实时流数据

### 28.3.1port

inport：

outport：默认端口

### 28.3.2properties

| 名称          | 展示名称      | 默认值 | 允许值 | 是否必填 | 描述               |
|---------------|---------------|--------|--------|----------|--------------------|
| hostname      | hostname      | “”     | 无     | 是       | socket 主机host名  |
| Port          | Port          | “”     | 无     | 是       | socket主机端口     |
| batchDuration | batchDuration | “”     | 无     | 否       | 获取数据的时间间隔 |
|               |               |        |        |          |                    |

## 28.4 SocketTextStreamByWindow

获取sokcet的实时窗口流数据

### 28.3.1port

inport：

outport：默认端口

### 28.3.2properties

| 名称           | 展示名称       | 默认值 | 允许值 | 是否必填 | 描述               |
|----------------|----------------|--------|--------|----------|--------------------|
| hostname       | hostname       | “”     | 无     | 是       | socket 主机host名  |
| Port           | Port           | “”     | 无     | 是       | socket主机端口     |
| batchDuration  | batchDuration  | “”     | 无     | 否       | 获取数据的时间间隔 |
| windowDuration | windowDuration | “”     | 无     | 是       | 窗口时间           |
| SlideDuration  | SlideDuration  | “”     | 无     | 是       | 滑动窗口           |

## 28.5 TextFileStream

获取text file的实时流数据

### 28.5.1port

inport：

outport：默认端口

### 28.5.2properties

| 名称          | 展示名称      | 默认值 | 允许值 | 是否必填 | 描述               |
|---------------|---------------|--------|--------|----------|--------------------|
| Directory     | Directory     | “”     | 无     | 是       | 文件夹路径         |
| batchDuration | batchDuration | “”     | 无     | 否       | 获取数据的时间间隔 |
|               |               |        |        |          |                    |
|               |               |        |        |          |                    |

# 28 Excel

## 28.1 excelParse

解析excel （xls ，xlsx）数据

### 28.1.1 port

inport：默认端口

outport：默认端口

### 28.1.2 properties

| 名称      | 展示名称  | 默认值 | 允许值 | 是否必填 | 描述          |
|-----------|-----------|--------|--------|----------|---------------|
| CachePath | CachePath |        | 无     | 是       | Json 保存路径 |

# 28 graphx

## 28.1 LabelPropagation

计算子图

### 28.1.1 port

inport：默认端口

outport：默认端口

### 28.1.2 properties

| 名称    | 展示名称 | 默认值 | 允许值 | 是否必填 | 描述 |
|---------|----------|--------|--------|----------|------|
| maxIter | maxIter  |        | 无     | 是       |      |

## 28.2 LoadGraph

构建图

### 28.1.1 port

inport：默认端口

outport：默认端口

### 28.1.2 properties

| 名称     | 展示名称 | 默认值 | 允许值 | 是否必填 | 描述 |
|----------|----------|--------|--------|----------|------|
| dataPath | dataPath |        | 无     | 是       |      |

# 29 Visualization

## 29.1 LineChar

线性图显示数据

### 29.1.1 port

inport：默认端口

outport：默认端口

### 29.1.2 properties

| 名称     | 展示名称 | 默认值 | 允许值 | 是否必填 | 描述   |
|----------|----------|--------|--------|----------|--------|
| Abscissa | Abscissa |        | 无     | 是       | 横坐标 |
|          |          |        |        |          |        |

维度需要采用自定义属性进行配置，如上游DataFrame的schema包括id，name，year，height，weight。那横坐标可以选择year，维度可以统计name的COUNT、height的AVG，weight的AVG。则自定义属性增加三个，key和CustomValue分别如下：

name:COUNT

height:AVG

weight:AVG

## 29.2 Histogram

柱状图显示数据

### 29.2.1 port

inport：默认端口

outport：默认端口

### 29.2.2 properties

| 名称     | 展示名称 | 默认值 | 允许值 | 是否必填 | 描述   |
|----------|----------|--------|--------|----------|--------|
| Abscissa | Abscissa |        | 无     | 是       | 横坐标 |
|          |          |        |        |          |        |

维度需要采用自定义属性进行配置，如上游DataFrame的schema包括id，name，year，height，weight。那横坐标可以选择year，维度可以统计name的COUNT、height的AVG，weight的AVG。则自定义属性增加三个，key和CustomValue分别如下：

name:COUNT

height:AVG

weight:AVG

## 29.3 ScatterPlogChart

散点图显示数据

### 29.3.1 port

inport：默认端口

outport：默认端口

### 29.3.2 properties

| 名称   | 展示名称 | 默认值 | 允许值 | 是否必填 | 描述 |
|--------|----------|--------|--------|----------|------|
| Legend | Legend   |        | 无     | 是       | 图例 |
|        |          |        |        |          |      |

自定义属性设置横坐标和维度。下图展示的按城市展示空气质量。

\+---+--------+---+--------+----+----+----+---+---+----------+

\| id\|province\|day\|AQIindex\|PM25\|PM10\| CO\|NO2\|SO2\|airQuality\|

\+---+--------+---+--------+----+----+----+---+---+----------+

\| 32\| 北京\| 1\| 55\| 9\| 56\|0.46\| 6\| 18\| 良\|

\| 33\| 北京\| 2\| 25\| 11\| 21\|0.65\| 9\| 34\| 优\|

\| 34\| 北京\| 3\| 56\| 7\| 63\| 0.3\| 5\| 14\| 良\|

\| 35\| 北京\| 4\| 33\| 7\| 29\|0.33\| 6\| 16\| 优\|

\| 36\| 北京\| 5\| 42\| 24\| 44\|0.76\| 16\| 40\| 优\|

\| 37\| 北京\| 6\| 82\| 58\| 90\|1.77\| 33\| 68\| 良\|

\| 38\| 北京\| 7\| 74\| 49\| 77\|1.46\| 27\| 48\| 良\|

\| 39\| 北京\| 8\| 78\| 55\| 80\|1.29\| 29\| 59\| 良\|

\| 40\| 北京\| 9\| 267\| 216\| 280\| 4.8\| 64\|108\| 重度污染\|

\| 41\| 北京\| 10\| 185\| 127\| 216\|2.52\| 27\| 61\| 中度污染\|

\+---+--------+---+--------+----+----+----+---+---+----------+

Legend设置为province，自定义属性设置时，key设置为day，AQIindex，PM25等，CustomValue有1进行递增，其中为1的列为横坐标，其他为维度。

{

"name": "ScatterPlotChart",

"bundle": "cn.piflow.bundle.visualization.ScatterPlotChart",

"uuid": "8a80da1b7618b26d017618b652b60006",

"properties": {

"legend": "province"

},

"customizedProperties": {

"SO2": "7",

"AQIindex": "2",

"NO2": "6",

"airQuality": "8",

"CO": "5",

"PM25": "3",

"PM10": "4",

"day": "1"

}

}

## 29.4 PieChart

饼状图显示数据

### 29.4.1 port

inport：默认端口

outport：默认端口

### 29.4.2 properties

| 名称            | 展示名称        | 默认值 | 允许值 | 是否必填 | 描述                           |
|-----------------|-----------------|--------|--------|----------|--------------------------------|
| dimension       | dimension       |        | 无     | 是       | 维度                           |
| indicator       | indicator       |        | 无     | 是       | 指标                           |
| indicatorOption | indicatorOption |        | 无     | 是       | 对指标的操作，包括COUNT、AVG等 |

## 29.5 TableShow

表格组件

### 29.5.1 port

inport：默认端口

outport：默认端口

### 29.5.2 properties

| 名称      | 展示名称  | 默认值 | 允许值 | 是否必填 | 描述                 |
|-----------|-----------|--------|--------|----------|----------------------|
| showField | ShowField | \*     | 无     | 是       | 以表格形式展示的字段 |
