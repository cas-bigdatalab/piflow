package cn.piflow.bundle.csv

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, CsvGroup, StopGroup}
import org.apache.spark.sql.SaveMode

class CsvSave extends ConfigurableStop{
  override val inportCount: Int = 1
  override val outportCount: Int = 0

  var csvSavePath: String = _
  var header: Boolean = _
  var delimiter: String = _

  override def setProperties(map: Map[String, Any]): Unit = {
    csvSavePath = MapUtil.get(map,"csvSavePath").asInstanceOf[String]
    header = MapUtil.get(map,"header").asInstanceOf[String].toBoolean
    delimiter = MapUtil.get(map,"delimiter").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    //csvSavePath
    val csvSavePath = new PropertyDescriptor().name("csvSavePath").displayName("csvSavePath").defaultValue("").required(true)
    descriptor = csvSavePath :: descriptor

    //header
    val header = new PropertyDescriptor().name("header").displayName("header").defaultValue("header").required(true)
    descriptor = header :: descriptor

    //delimiter
    val delimiter = new PropertyDescriptor().name("delimiter").displayName("delimiter").defaultValue(",").required(true)
    descriptor = delimiter :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("./src/main/resources/selectHiveQL.jpg")
  }

  override def getGroup(): StopGroup = {
    CsvGroup
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val df = in.read()
    df.show()
    df.write
      .format("csv")
      .mode(SaveMode.Overwrite)
      .option("header", header)
      .save(csvSavePath)
  }
}

