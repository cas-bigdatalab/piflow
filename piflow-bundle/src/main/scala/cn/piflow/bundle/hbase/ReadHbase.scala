package cn.piflow.bundle.hbase

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.hadoop.hbase.mapreduce.TableInputFormat
import org.apache.hadoop.hbase.util.Bytes
import org.apache.spark.sql.types.{StringType, StructField, StructType}
import org.apache.spark.sql.{Row, SparkSession}
import org.apache.hadoop.hbase.HBaseConfiguration

import scala.collection.mutable.ArrayBuffer

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
class ReadHbase extends ConfigurableStop{

  override val authorEmail: String = "ygang@cnic.cn"
  override val description: String = "Read data from Hbase"
  override val inportList: List[String] = List(Port.DefaultPort)
  override val outportList: List[String] = List(Port.DefaultPort)

  var zookeeperQuorum  :String= _
  var zookeeperClientPort  :String= _
  var tablename  :String= _
  var rowkey  :String= _
  var columnFamily: String = _
  var columnQualifier  :String= _

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val spark = pec.get[SparkSession]()
    val sc = spark.sparkContext

    val hbaseConf = HBaseConfiguration.create()
    hbaseConf.set("hbase.zookeeper.quorum", zookeeperQuorum) //设置zooKeeper集群地址，也可以通过将hbase-site.xml导入classpath，但是建议在程序里这样设置
    hbaseConf.set("hbase.zookeeper.property.clientPort", zookeeperClientPort) //设置zookeeper连接端口，默认2181
    hbaseConf.set(TableInputFormat.INPUT_TABLE, tablename)

    //读取数据并转化成rdd TableInputFormat 是 org.apache.hadoop.hbase.mapreduce 包下的
    val hBaseRDD= sc.newAPIHadoopRDD(hbaseConf, classOf[TableInputFormat],
      classOf[org.apache.hadoop.hbase.io.ImmutableBytesWritable],
      classOf[org.apache.hadoop.hbase.client.Result])

    val schema: Array[String] = columnQualifier.split(",").map(x=>x.trim)
    val families=columnFamily.split(",").map(x=>x.trim)

    val col_str=rowkey+","+ columnQualifier
    val newSchema:Array[String]=col_str.split(",")

    val fields: Array[StructField] = newSchema.map(d=>StructField(d,StringType,nullable = true))
    val dfSchema: StructType = StructType(fields)


    val kv = hBaseRDD.map(r => {
      val rowkey = Bytes.toString(r._2.getRow)
      val row = new ArrayBuffer[String]
      row += rowkey
      if(families.size==1){
        schema.foreach(c => {
          val fields = Bytes.toString(r._2.getValue(Bytes.toBytes(columnFamily), Bytes.toBytes(c)))
          row += fields

        })
      }else{
        families.foreach(f=>{
          schema.foreach(c => {
            val fields = Bytes.toString(r._2.getValue(Bytes.toBytes(f), Bytes.toBytes(c)))
            if (fields==null){
              row
            }else{
              row += fields
            }
          })
        })
      }
      Row.fromSeq(row.toArray.toSeq)
    })
    val df=spark.createDataFrame(kv,dfSchema)

    out.write(df)

  }
  override def setProperties(map: Map[String, Any]): Unit = {
    zookeeperQuorum=MapUtil.get(map,key="zookeeperQuorum").asInstanceOf[String]
    zookeeperClientPort=MapUtil.get(map,key="zookeeperClientPort").asInstanceOf[String]
    tablename=MapUtil.get(map,key="tablename").asInstanceOf[String]
    rowkey=MapUtil.get(map,key="rowkey").asInstanceOf[String]
    columnFamily=MapUtil.get(map,key="columnFamily").asInstanceOf[String]
    columnQualifier=MapUtil.get(map,key="columnQualifier").asInstanceOf[String]

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

    val columnQualifier = new PropertyDescriptor()
      .name("columnQualifier")
      .displayName("columnQualifier")
      .defaultValue("")
      .description("Column Qualifier")
      .required(true)
      .example("name,age")
    descriptor = columnQualifier :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/hbase/GetHbase.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.HbaseGroup)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }
}
