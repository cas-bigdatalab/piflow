package cn.piflow.bundle.excel

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.SparkSession

class ExcelRead extends ConfigurableStop{
  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "Create a DataFrame from an Excel file"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var filePath: String = _
  var header: String = _
  var dataAddress: String = _
  //  var setErrorCellsToFallbackValues: String = _
  //  var timestampFormat: String = _
  //  var excerptSize: String = _

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()

    val frame = spark.read
      .format("com.crealytics.spark.excel")
      .option("dataAddress",dataAddress)
      //      .option("setErrorCellsToFallbackValues", setErrorCellsToFallbackValues)
      //      .option("timestampFormat", timestampFormat)
      //      .option("excerptSize", excerptSize.toInt)
      .option("header", header)
      .load(filePath)

    out.write(frame)
  }

  override def setProperties(map: Map[String, Any]): Unit = {
    filePath = MapUtil.get(map,"filePath").asInstanceOf[String]
    header = MapUtil.get(map,"header").asInstanceOf[String]
    dataAddress = MapUtil.get(map,"dataAddress").asInstanceOf[String]
    //    setErrorCellsToFallbackValues = MapUtil.get(map,"setErrorCellsToFallbackValues").asInstanceOf[String]
    //    timestampFormat = MapUtil.get(map,"timestampFormat").asInstanceOf[String]
    //    excerptSize = MapUtil.get(map,"excerptSize").asInstanceOf[String]
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
      .defaultValue("'Sheet1'!")
      .required(true)
      .example("'Sheet1'!")
    descriptor = dataAddress :: descriptor

    //    val setErrorCellsToFallbackValues = new PropertyDescriptor()
    //      .name("setErrorCellsToFallbackValues")
    //      .displayName("setErrorCellsToFallbackValues")
    //      .description("default: false, where errors will be converted to null. If true, any ERROR cell values (e.g. #N/A) will be converted to the zero values of the column's data type.")
    //      .defaultValue("false")
    //      .required(false)
    //      .example("fales")
    //    descriptor = setErrorCellsToFallbackValues :: descriptor
    //
    //
    //    val timestampFormat = new PropertyDescriptor()
    //      .name("timestampFormat")
    //      .displayName("timestampFormat")
    //      .description("default: yyyy-mm-dd hh:mm:ss[.fffffffff]")
    //      .defaultValue("yyyy-mm-dd hh:mm:ss")
    //      .required(true)
    //      .example("yyyy-mm-dd hh:mm:ss")
    //    descriptor = timestampFormat :: descriptor
    //
    //    val excerptSize = new PropertyDescriptor()
    //      .name("excerptSize")
    //      .displayName("excerptSize")
    //      .description("default: 10. If set and if schema inferred, number of rows to infer schema from")
    //      .defaultValue("10")
    //      .required(true)
    //      .example("10")
    //    descriptor = excerptSize :: descriptor

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
