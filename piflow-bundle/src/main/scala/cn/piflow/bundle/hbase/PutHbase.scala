package cn.piflow.bundle.hbase

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.hadoop.hbase.HBaseConfiguration
import org.apache.hadoop.hbase.client.{Put, Result}
import org.apache.hadoop.hbase.io.ImmutableBytesWritable
import org.apache.hadoop.hbase.mapred.TableOutputFormat
import org.apache.hadoop.hbase.util.Bytes
import org.apache.hadoop.mapred.JobConf
import org.apache.hadoop.mapreduce.Job
import org.apache.spark.sql.SparkSession

/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 *
 * Copyright (c) 2022 πFlow. All rights reserved.
 */
class PutHbase extends ConfigurableStop{

  override val authorEmail: String = "ygang@cnic.cn"
  override val description: String = "Put data to Hbase"
  override val inportList: List[String] = List(Port.DefaultPort)
  override val outportList: List[String] = List(Port.DefaultPort)

  var zookeeperQuorum  :String= _
  var zookeeperClientPort  :String= _
  var tablename  :String= _
  var rowkey  :String= _
  var columnFamily: String = _

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val df = in.read()

    val hbaseConf = HBaseConfiguration.create()
    hbaseConf.set("hbase.zookeeper.quorum",zookeeperQuorum)  //设置zooKeeper集群地址，也可以通过将hbase-site.xml导入classpath，但是建议在程序里这样设置
    hbaseConf.set("hbase.zookeeper.property.clientPort", zookeeperClientPort)       //设置zookeeper连接端口，默认2181
    hbaseConf.set(TableOutputFormat.OUTPUT_TABLE, tablename)

    // 初始化job，TableOutputFormat 是 org.apache.hadoop.hbase.mapred 包下的
    val jobConf = new JobConf(hbaseConf)
    jobConf.setOutputFormat(classOf[TableOutputFormat])
    jobConf.setOutputKeyClass(classOf[ImmutableBytesWritable])
    jobConf.setOutputValueClass(classOf[Result])

    val columnQualifier = df.schema.fieldNames
    df.rdd.map(row =>{
      val rowid = nullHandle(row.getAs[String](rowkey))
      /*一个Put对象就是一行记录，在构造方法中指定主键
      * 所有插入的数据 须用 org.apache.hadoop.hbase.util.Bytes.toBytes 转换
      * Put.addColumn 方法接收三个参数：列族，列名，数据*/
      val p = new Put(Bytes.toBytes(rowid))

      columnQualifier.foreach(a=>{
        val value = nullHandle(row.getAs[String](a))
        p.addColumn(Bytes.toBytes(columnFamily),Bytes.toBytes(a),Bytes.toBytes(value))
      })
      (new ImmutableBytesWritable,p)
    }).saveAsHadoopDataset(jobConf)


  }
  def nullHandle(str:String):String={
    if (str == null || "".equals(str)){
      return "null"
    }else {
      return str
    }
  }
  override def setProperties(map: Map[String, Any]): Unit = {
    zookeeperQuorum=MapUtil.get(map,key="zookeeperQuorum").asInstanceOf[String]
    zookeeperClientPort=MapUtil.get(map,key="zookeeperClientPort").asInstanceOf[String]
    tablename=MapUtil.get(map,key="tablename").asInstanceOf[String]
    rowkey=MapUtil.get(map,key="rowkey").asInstanceOf[String]
    columnFamily=MapUtil.get(map,key="columnFamily").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val zookeeperQuorum = new PropertyDescriptor()
      .name("zookeeperQuorum")
      .displayName("zookeeperQuorum")
      .defaultValue("")
      .description("Zookeeper cluster address")
      .required(true)
      .example("10.0.0.101,10.0.0.102,10.0.0.103")
    descriptor = zookeeperQuorum :: descriptor

    val zookeeperClientPort = new PropertyDescriptor()
      .name("zookeeperClientPort")
      .displayName("zookeeperClientPort")
      .defaultValue("2181")
      .description("Zookeeper connection port")
      .required(true)
      .example("2181")
    descriptor = zookeeperClientPort :: descriptor

    val tablename = new PropertyDescriptor()
      .name("tablename")
      .displayName("tablename")
      .defaultValue("")
      .description("Table in Hbase")
      .required(true)
      .example("sparkdemo")
    descriptor = tablename :: descriptor

    val rowkey = new PropertyDescriptor()
      .name("rowkey")
      .displayName("rowkey")
      .defaultValue("")
      .description("Rowkey of table in Hbase")
      .required(true)
      .example("rowkey")
    descriptor = rowkey :: descriptor

    val columnFamily = new PropertyDescriptor()
      .name("columnFamily")
      .displayName("columnFamily")
      .defaultValue("")
      .description("The column family of table,multiple column families are separated by commas")
      .required(true)
      .example("cf1")
    descriptor = columnFamily :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/hbase/PutHbase.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.HbaseGroup)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }
}
