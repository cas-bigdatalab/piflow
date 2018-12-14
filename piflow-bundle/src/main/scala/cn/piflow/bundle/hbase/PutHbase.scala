package cn.piflow.bundle.Hbase

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.ImageUtil
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.hbase.HBaseConfiguration
import org.apache.hadoop.hbase.client.Put
import org.apache.hadoop.hbase.io.ImmutableBytesWritable
import org.apache.hadoop.hbase.mapred.TableOutputFormat
import org.apache.hadoop.hbase.util.Bytes
import org.apache.hadoop.mapred.JobConf
import org.apache.spark.sql.SparkSession


// Caused by: java.lang.ClassNotFoundException: org.apache.hadoop.hbase.io.ImmutableBytesWritable

class PutHbase extends ConfigurableStop {
  val authorEmail: String = "ygang@cnic.cn"

  override val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  override val outportList: List[String] = List(PortEnum.NonePort.toString)
  override val description: String = "put data  to hbase "


  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val sc = spark.sparkContext
    val inDf = in.read()
    inDf.show()

    val tableName = "User1"

    val configuration: Configuration = HBaseConfiguration.create()
    // 使用 configuration 配置参数
    configuration.set("hbase.zookeeper.quorum", "10.0.86.89,10.0.86.90,10.0.86.91")
    configuration.set("hbase.zookeeper.property.clientPort","2181")


    val jobConf= new JobConf(configuration)
    jobConf.setOutputFormat(classOf[TableOutputFormat])
    jobConf.setOutputKeyClass(classOf[ImmutableBytesWritable])
    jobConf.set(TableOutputFormat.OUTPUT_TABLE,tableName)

    val indataRdd = sc.makeRDD(Array("3,rongcheng,M,29","4,guanhua,M,27"))

    val rdd = indataRdd.map(_.split(",")).map { arr => {
      val put = new Put(Bytes.toBytes(arr(0)))

      put.addColumn(Bytes.toBytes("info"), Bytes.toBytes("name"), Bytes.toBytes(arr(1)))
      put.addColumn(Bytes.toBytes("info"), Bytes.toBytes("gender"), Bytes.toBytes(arr(2)))
      put.addColumn(Bytes.toBytes("info"), Bytes.toBytes("age"), Bytes.toBytes(arr(3)))

      (new ImmutableBytesWritable, put)
    }
    }

    rdd.saveAsHadoopDataset(jobConf)

  }


  def initialize(ctx: ProcessContext): Unit = {

  }

  def setProperties(map : Map[String, Any]): Unit = {
    //    es_nodes=MapUtil.get(map,key="es_nodes").asInstanceOf[String]
    //    port=MapUtil.get(map,key="port").asInstanceOf[String]
    //    es_index=MapUtil.get(map,key="es_index").asInstanceOf[String]
    //    es_type=MapUtil.get(map,key="es_type").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val es_nodes = new PropertyDescriptor().name("es_nodes").displayName("REDIS_HOST").defaultValue("").required(true)
    val port = new PropertyDescriptor().name("port").displayName("PORT").defaultValue("").required(true)
    val es_index = new PropertyDescriptor().name("es_index").displayName("ES_INDEX").defaultValue("").required(true)
    val es_type = new PropertyDescriptor().name("es_type").displayName("ES_TYPE").defaultValue("").required(true)


    descriptor = es_nodes :: descriptor
    descriptor = port :: descriptor
    descriptor = es_index :: descriptor
    descriptor = es_type :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("hbase.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.HbaseGroup.toString)
  }

}
