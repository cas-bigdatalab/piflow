package cn.piflow.bundle.excel

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.functions.col


class ExcelWriteSort extends ConfigurableStop{
  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "Write DataFrame into an Excel file (custom sorting)"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var filePath: String = _
  var header: String = _
  var dataAddress: String = _
  var saveMode: String = _
  var sortField:String = _
  var sortOrder:String = _

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    var df = in.read()

    val cols: Seq[String] = Seq(sortField.split(","): _*)

    if(sortOrder.equals("asc")){
      df  =  df.repartition(1).orderBy(cols.map(col).map(_.asc): _*)
    } else {
      df  =  df.repartition(1).orderBy(cols.map(col).map(_.desc): _*)
    }
    df.write
      .format("com.crealytics.spark.excel")
      .option("dataAddress",dataAddress)
      //      .option("timestampFormat", timestampFormat)
      .option("header", header)
      .mode(saveMode)
      .save(filePath)
  }

  override def setProperties(map: Map[String, Any]): Unit = {
    filePath = MapUtil.get(map,"filePath").asInstanceOf[String]
    header = MapUtil.get(map,"header").asInstanceOf[String]
    dataAddress = MapUtil.get(map,"dataAddress").asInstanceOf[String]
    saveMode = MapUtil.get(map,"saveMode").asInstanceOf[String]

    sortField = MapUtil.get(map,"sortField").asInstanceOf[String]
    sortOrder = MapUtil.get(map,"sortOrder").asInstanceOf[String]
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

    val dataAddress = new PropertyDescriptor()
      .name("dataAddress")
      .displayName("DataAddress")
            .description("The location of data to read or write can be specified with the dataAddress option, Currently the following address styles are supported:" +
              "A1: Start cell of the data. Reading will return all rows below and all columns to the right. Writing will start here and use as many columns and rows as required.\n" +
              "'My Sheet'!A1: Same as above, but with a specific sheet.\n" +
              "A1:F35: Cell range of data. Reading will return only rows and columns in the specified range. Writing will start in the first cell (B3 in this example) " +
              "and use only the specified columns and rows. If there are more rows or columns in the DataFrame to write, they will be truncated. Make sure this is what you want.\n" +
              "'My Sheet'!A1:F35: Same as above, but with a specific sheet.")
      .defaultValue("A1")
      .required(true)
      .example("A1")
    descriptor = dataAddress :: descriptor

    val saveMode = new PropertyDescriptor()
      .name("saveMode")
      .displayName("saveMode")
      .description("default: overwrite")
      .defaultValue("overwrite")
      .allowableValues(Set("append","overwrite"))
      .required(true)
      .example("overwrite")
    descriptor = saveMode :: descriptor

    val sortField = new PropertyDescriptor()
      .name("sortField")
      .displayName("sortField")
      .description("排序字段")
      .defaultValue("")
      .required(true)
      .example("id")
    descriptor = sortField :: descriptor

    val sortOrder = new PropertyDescriptor()
      .name("sortOrder")
      .displayName("sortOrder")
      .description("排序方式：默认升序")
      .defaultValue("asc")
      .allowableValues(Set("asc","desc"))
      .required(true)
      .example("asc")
    descriptor = sortOrder :: descriptor

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
