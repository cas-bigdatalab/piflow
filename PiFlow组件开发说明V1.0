# Piflow组件开发说明书

## 样例

请下载样例工程，并参考ShowData组件进行开发，依赖包piflow-configure.jar在lib目录下  
<https://github.com/cas-bigdatalab/piflowExternal>

请注意getIcon函数的调用方式有所更改：ImageUtil.getImage("icon/csv/CsvParser.png", this.getClass.getName)  
![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V0.8/stop_dev/1.png?raw=true)

## 1.1环境要求

1.开发工具Intellij IDEA

2.语言要求jdk 1.8，scala 2.11.8

3.集群环境部署Hadoop2.7.0，Spark2.1.0（可根据实际情况部署进行修改）

## 1.2 独立开发步骤

### 1.2.1 新建Maven工程

1.  导入piflow-configure.jar包

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V0.8/stop_dev/2.png?raw=true)

1.  修改pom.xml文件如下
```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>piflow</groupId>
    <artifactId>piflow-external</artifactId>
    <version>1.0-SNAPSHOT</version>

    <properties>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <jetty.version>9.0.0.M0</jetty.version>
        <spark.version>2.2.0</spark.version>
        <scala.version>2.11.8</scala.version>
        <java.version>1.8</java.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.scala-lang</groupId>
            <artifactId>scala-library</artifactId>
            <version>${scala.version}</version>
        </dependency>
        <dependency>
            <groupId>org.scala-lang</groupId>
            <artifactId>scala-reflect</artifactId>
            <version>${scala.version}</version>
        </dependency>
        <dependency>
            <groupId>org.scala-lang</groupId>
            <artifactId>scala-compiler</artifactId>
            <version>${scala.version}</version>
        </dependency>
        <dependency>
            <groupId>junit</groupId>
            <artifactId>junit</artifactId>
            <version>4.11</version>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.apache.spark</groupId>
            <artifactId>spark-core_2.11</artifactId>
            <version>${spark.version}</version>
        </dependency>
        <dependency>
            <groupId>org.apache.spark</groupId>
            <artifactId>spark-sql_2.11</artifactId>
            <version>${spark.version}</version>
        </dependency>
        <dependency>
            <groupId>org.apache.spark</groupId>
            <artifactId>spark-hive_2.11</artifactId>
            <version>${spark.version}</version>
        </dependency>
        <dependency>
            <groupId>org.apache.spark</groupId>
            <artifactId>spark-yarn_2.11</artifactId>
            <version>${spark.version}</version>
        </dependency>
        <dependency>
            <groupId>org.apache.spark</groupId>
            <artifactId>spark-streaming_2.11</artifactId>
            <version>${spark.version}</version>
        </dependency>
        <dependency>
            <groupId>org.apache.spark</groupId>
            <artifactId>spark-streaming-kafka-0-10_2.11</artifactId>
            <version>${spark.version}</version>
        </dependency>
        <dependency>
            <groupId>org.apache.spark</groupId>
            <artifactId>spark-streaming-flume_2.11</artifactId>
            <version>${spark.version}</version>
        </dependency>
        <dependency>
            <groupId>org.mongodb.spark</groupId>
            <artifactId>mongo-spark-connector_2.11</artifactId>
            <version>${spark.version}</version>
        </dependency>
        <dependency>
            <groupId>org.apache.spark</groupId>
            <artifactId>spark-mllib_2.11</artifactId>
            <version>${spark.version}</version>
        </dependency>
        <dependency>
            <groupId>org.apache.kafka</groupId>
            <artifactId>kafka-clients</artifactId>
            <version>2.1.1</version>
        </dependency>
        <dependency>
            <groupId>org.apache.kafka</groupId>
            <artifactId>kafka_2.11</artifactId>
            <version>2.1.1</version>
        </dependency>
        <dependency>
            <groupId>com.h2database</groupId>
            <artifactId>h2</artifactId>
            <version>1.4.197</version>
        </dependency>
        <dependency>
            <groupId>org.apache.httpcomponents</groupId>
            <artifactId>httpcore</artifactId>
            <version>4.4</version>
        </dependency>

    </dependencies>
    <build>

        <plugins>

            <plugin>
                <groupId>net.alchim31.maven</groupId>
                <artifactId>scala-maven-plugin</artifactId>
                <version>3.2.2</version>
                <executions>
                    <execution>
                        <id>Scaladoc</id>
                        <goals>
                            <goal>doc</goal>
                        </goals>
                        <phase>prepare-package</phase>
                        <configuration>
                            <args>
                                <arg>-no-link-warnings</arg>
                            </args>
                        </configuration>
                    </execution>
                    <execution>
                        <id>compile</id>
                        <goals>
                            <goal>compile</goal>
                            <goal>testCompile</goal>
                        </goals>
                        <configuration>
                            <args>
                                <arg>-dependencyfile</arg>
                                <arg>${project.build.directory}/.scala_dependencies</arg>
                            </args>
                        </configuration>
                        <phase>compile</phase>
                    </execution>

                    <execution>
                        <phase>process-resources</phase>
                        <goals>
                            <goal>compile</goal>
                        </goals>
                    </execution>
                </executions>
            </plugin>

        </plugins>
    </build>
</project>
```



### 1.2.2 开发Stop

1.新建package cn.piflow.bundle

2.新建Stop extends ConfigurableStop，并实现对应方法

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V0.8/stop_dev/3.png?raw=true)

### build jar 包

首先选择File-\>Project Structure

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V0.8/stop_dev/4.png?raw=true)

然后点击Artifacts，添加“+”添加空白的jar

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V0.8/stop_dev/5.png?raw=true)

点击“+”，下拉框选择Module Output

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V0.8/stop_dev/6.png?raw=true)

在弹出框中选择module

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V0.8/stop_dev/7.png?raw=true)

修改jar的名称

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V0.8/stop_dev/8.png?raw=true)

点击Build-\>Build Artifacts，build jar包

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V0.8/stop_dev/9.png?raw=true)

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V0.8/stop_dev/10.png?raw=true)

最终build jar包在工程的out/artifacts/目录下

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V0.8/stop_dev/11.png?raw=true)

### 发布jar包

1.  V0.8及以上版本：StopHub列表中点击上传按钮进行上传，上传成功之后进行Mount操作。成功后在流水线配置页面即可显示该jar中对应的数据处理组件

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V0.8/stop_dev/13.png?raw=true)

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V0.8/stop_dev/14.png?raw=true)

## 1.3 PiFlowServer中的开发步骤

在PiFlow-bundle模块中新建类，继承ConfigurableStop并实现对应接口，具体参考样例小节。完成后build
jar包并替换piflow-server.jar,重启服务即可。

![](https://github.com/cas-bigdatalab/piflow/blob/master/doc/V0.8/stop_dev/15.png?raw=true)
