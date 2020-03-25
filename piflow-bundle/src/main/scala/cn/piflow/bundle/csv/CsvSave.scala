package cn.piflow.bundle.csv

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf._
import org.apache.spark.sql.SaveMode

class CsvSave extends ConfigurableStop{
  val authorEmail: String = "xjzhu@cnic.cn"
  val description: String = "Save data into csv file."
  val inportList: List[String] = List(Port.DefaultPort.toString)
  val outportList: List[String] = List(Port.DefaultPort.toString)

  var csvSavePath: String = _
  var header: Boolean = _
  var delimiter: String = _
  var partition :String= _

  override def setProperties(map: Map[String, Any]): Unit = {
    csvSavePath = MapUtil.get(map,"csvSavePath").asInstanceOf[String]
    header = MapUtil.get(map,"header").asInstanceOf[String].toBoolean
    delimiter = MapUtil.get(map,"delimiter").asInstanceOf[String]
    partition = MapUtil.get(map,key="partition").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val csvSavePath = new PropertyDescriptor()
      .name("csvSavePath")
      .displayName("CsvSavePath")
      .description("The save path of csv file")
      .defaultValue("")
      .required(true)
      .example("")
    descriptor = csvSavePath :: descriptor

    val header = new PropertyDescriptor()
      .name("header")
      .displayName("Header")
      .description("Whether the csv file has a header")
      .defaultValue("")
      .required(true)
    descriptor = header :: descriptor

    val delimiter = new PropertyDescriptor()
      .name("delimiter")
      .displayName("Delimiter")
      .description("The delimiter of csv file")
      .defaultValue(",")
      .required(true)
      .example("")
    descriptor = delimiter :: descriptor

    val partition = new PropertyDescriptor()
      .name("partition")
      .displayName("Partition")
      .description("The partition of csv file")
      .defaultValue("1")
      .required(true)
      .example("")
    descriptor = partition :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/csv/CsvSave.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.CsvGroup)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val df = in.read()
    df.repartition(partition.toInt).write
      .format("csv")
      .mode(SaveMode.Overwrite)
      .option("header", header)
      .option("delimiter",delimiter)
      .save(csvSavePath)
  }
}

