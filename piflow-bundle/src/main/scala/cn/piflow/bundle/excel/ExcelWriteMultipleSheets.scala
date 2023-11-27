package cn.piflow.bundle.excel

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}

class ExcelWriteMultipleSheets extends ConfigurableStop{
  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "Write multiple DataFrames into multiple sheets of the same Excel file"
  val inportList: List[String] = List(Port.AnyPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var filePath: String = _
  var header: String = _

  var inports : List[String] = _

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    inports.foreach(x=>{
      val df = in.read(x)
      df.write
        .format("com.crealytics.spark.excel")
        .option("dataAddress",s"'${x}'!A1")
        .option("header", header)
        .mode("append")
        .save(filePath)
    })
  }

  override def setProperties(map: Map[String, Any]): Unit = {
    val inportStr = MapUtil.get(map,"inports").asInstanceOf[String]
    inports = inportStr.split(",").map(x => x.trim).toList

    filePath = MapUtil.get(map,"filePath").asInstanceOf[String]
    header = MapUtil.get(map,"header").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val filePath = new PropertyDescriptor()
      .name("filePath")
      .displayName("FilePath")
      .description("The path of excel file")
      .defaultValue("")
      .required(true)
      .example("/test/test.xlsx")
    descriptor = filePath :: descriptor

    val header = new PropertyDescriptor()
      .name("header")
      .displayName("Header")
      .description("Whether the excel file has a header")
      .defaultValue("true")
      .allowableValues(Set("true","false"))
      .required(true)
      .example("true")
    descriptor = header :: descriptor

    val inports = new PropertyDescriptor()
      .name("inports")
      .displayName("inports")
      .description("Inports string are separated by commas")
      .defaultValue("")
      .required(true)
    descriptor = inports :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/excel/excelParse.png",this.getClass.getName)
  }

  override def getGroup(): List[String] = {
    List(StopGroup.ExcelGroup)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

}
