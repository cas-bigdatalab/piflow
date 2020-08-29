package cn.piflow.bundle.hdfs

import cn.piflow._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import org.apache.spark.sql.SparkSession


class GetHdfs extends ConfigurableStop{
  override val authorEmail: String = "ygang@cnic.com"
  override val description: String = "Get data from hdfs"
  override val inportList: List[String] = List(Port.DefaultPort)
  override val outportList: List[String] = List(Port.DefaultPort)

  var hdfsUrl : String=_
  var hdfsPath :String= _
  var types :String = _

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val sc= spark.sparkContext
    import spark.implicits._

    val path = hdfsUrl+hdfsPath

      if (types == "json") {
        val df = spark.read.json(path)
        df.schema.printTreeString()
        out.write(df)

      } else if (types == "csv") {
        val df = spark.read.csv(path)
        df.schema.printTreeString()
        out.write(df)

      }else if (types == "parquet") {
        val df = spark.read.csv(path)
        df.schema.printTreeString()
        out.write(df)

      }else if (types == "orc"){
        val df = spark.read.orc(path)
        df.schema.printTreeString()
        out.write(df)
      }
      else {
        val rdd = sc.textFile(path)
        val outDf = rdd.toDF()
        outDf.schema.printTreeString()
        out.write(outDf)

    }
  }
  override def setProperties(map: Map[String, Any]): Unit = {
    hdfsUrl = MapUtil.get(map,key="hdfsUrl").asInstanceOf[String]
    hdfsPath = MapUtil.get(map,key="hdfsPath").asInstanceOf[String]
    types = MapUtil.get(map,key="types").asInstanceOf[String]
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

    val types = new PropertyDescriptor().
      name("types")
      .displayName("Types")
      .description("The type of file you want to load")
      .defaultValue("csv")
      .allowableValues(Set("txt","parquet","csv","json","orc"))
      .required(true)
        .example("csv")
    descriptor = types :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/hdfs/GetHdfs.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.HdfsGroup)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }
}
