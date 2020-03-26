package cn.piflow.bundle.hdfs


import cn.piflow._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.FileSystem
import org.apache.spark.sql.SparkSession

class PutHdfs extends ConfigurableStop{

  override val authorEmail: String = "ygang@cnic.com"
  override val description: String = "Put data into hdfs"
  override val inportList: List[String] = List(Port.DefaultPort)
  override val outportList: List[String] = List(Port.DefaultPort)

  var hdfsPath :String= _
  var hdfsUrl :String= _
  var types :String= _
  var partition :String= _

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val inDF = in.read()

    val config = new Configuration()
    config.set("fs.defaultFS",hdfsUrl)
    val fs = FileSystem.get(config)

    if (types=="json"){
      inDF.repartition(partition.toInt).write.json(hdfsUrl+hdfsPath)
    } else if (types=="csv"){
      inDF.repartition(partition.toInt).write.csv(hdfsUrl+hdfsPath)
    } else {
      //parquet
      inDF.repartition(partition.toInt).write.save(hdfsUrl+hdfsPath)
    }

  }
  override def setProperties(map: Map[String, Any]): Unit = {
    hdfsUrl = MapUtil.get(map,key="hdfsUrl").asInstanceOf[String]
    hdfsPath = MapUtil.get(map,key="hdfsPath").asInstanceOf[String]
    types = MapUtil.get(map,key="types").asInstanceOf[String]
    partition = MapUtil.get(map,key="partition").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val hdfsPath = new PropertyDescriptor()
      .name("hdfsPath")
      .displayName("HdfsPath")
      .defaultValue("")
      .description("File path of HDFS")
      .required(true)
      .example("/work/")
    descriptor = hdfsPath :: descriptor

    val hdfsUrl = new PropertyDescriptor()
      .name("hdfsUrl")
      .displayName("HdfsUrl")
      .defaultValue("")
      .description("URL address of HDFS")
      .required(true)
      .example("hdfs://192.168.3.138:8020")
    descriptor = hdfsUrl :: descriptor

    val types = new PropertyDescriptor()
      .name("types")
      .displayName("Types")
      .description("The format you want to write is json,csv,parquet")
      .defaultValue("csv")
      .allowableValues(Set("json","csv","parquet"))
      .required(true)
      .example("csv")
    descriptor = types :: descriptor

    val partition = new PropertyDescriptor()
      .name("partition")
      .displayName("Partition")
      .description("Write several partitions")
      .defaultValue("1")
      .required(true)
      .example("1")
    descriptor = partition :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/hdfs/PutHdfs.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.HdfsGroup)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }


}
