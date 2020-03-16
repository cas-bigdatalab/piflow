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
  override val inportList: List[String] = List(Port.DefaultPort.toString)
  override val outportList: List[String] = List(Port.DefaultPort.toString)
  override val description: String = "Put data to hdfs"

  var hdfsPath :String= _
  var hdfsUrl :String= _
  var types :String= _
  var partition :Int= _

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val inDF = in.read()

    val config = new Configuration()
    config.set("fs.defaultFS",hdfsUrl)
    val fs = FileSystem.get(config)

    if (types=="json"){
      inDF.repartition(partition).write.json(hdfsUrl+hdfsPath)
    } else if (types=="csv"){
      inDF.repartition(partition).write.csv(hdfsUrl+hdfsPath)
    } else {
      //parquet
      inDF.repartition(partition).write.save(hdfsUrl+hdfsPath)
    }

  }
  override def setProperties(map: Map[String, Any]): Unit = {
    hdfsUrl = MapUtil.get(map,key="hdfsUrl").asInstanceOf[String]
    hdfsPath = MapUtil.get(map,key="hdfsPath").asInstanceOf[String]
    types = MapUtil.get(map,key="types").asInstanceOf[String]
    partition = MapUtil.get(map,key="partition").asInstanceOf[Int]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val hdfsPath = new PropertyDescriptor().name("hdfsPath").displayName("hdfsPath").defaultValue("").required(true)
    val hdfsUrl = new PropertyDescriptor().name("hdfsUrl").displayName("hdfsUrl").defaultValue("").required(true)
    val types = new PropertyDescriptor().name("types").displayName("json,csv,parquet").description("json,csv,parquet")
      .defaultValue("csv").allowableValues(Set("json","csv","parquet")).required(true)

    val partition = new PropertyDescriptor().name("partition").displayName("repartition").description("partition").defaultValue("").required(true)
    descriptor = partition :: descriptor
    descriptor = types :: descriptor
    descriptor = hdfsPath :: descriptor
    descriptor = hdfsUrl :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/hdfs/PutHdfs.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.HdfsGroup.toString)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }


}
