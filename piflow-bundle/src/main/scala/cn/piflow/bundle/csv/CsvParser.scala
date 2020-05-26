package cn.piflow.bundle.csv

import cn.piflow._
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.sql.types.{StringType, StructField, StructType}
import org.apache.spark.sql.{DataFrame, SparkSession}


class CsvParser extends ConfigurableStop{

  val authorEmail: String = "xjzhu@cnic.cn"
  val description: String = "Parse csv file or folder"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var csvPath: String = _
  var header: Boolean = _
  var delimiter: String = _
  var schema: String = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val spark = pec.get[SparkSession]()
    var csvDF:DataFrame = null
    if (header){
      csvDF = spark.read
        .option("header",header)
        .option("inferSchema","true")
        .option("delimiter",delimiter)
        .csv(csvPath)

    }else{

      val field = schema.split(",").map(x => x.trim)
      val structFieldArray : Array[StructField] = new Array[StructField](field.size)
      for(i <- 0 to field.size - 1){
        structFieldArray(i) = new StructField(field(i), StringType, nullable = true)
      }
      val schemaStructType = StructType(structFieldArray)

      csvDF = spark.read
        .option("header",header)
        .option("inferSchema","false")
        .option("delimiter",delimiter)
        .option("timestampFormat","yyyy/MM/dd HH:mm:ss ZZ")
        .schema(schemaStructType)
        .csv(csvPath)
    }
    out.write(csvDF)

  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  def setProperties(map : Map[String, Any]): Unit = {
    csvPath = MapUtil.get(map,"csvPath").asInstanceOf[String]
    header = MapUtil.get(map,"header").asInstanceOf[String].toBoolean
    delimiter = MapUtil.get(map,"delimiter").asInstanceOf[String]
    schema = MapUtil.get(map,"schema").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val csvPath = new PropertyDescriptor()
      .name("csvPath")
      .displayName("CsvPath")
      .description("The path of csv file or folder")
      .defaultValue("")
      .required(true)
      .example("hdfs://127.0.0.1:9000/test/")
    descriptor = csvPath :: descriptor

    val header = new PropertyDescriptor()
      .name("header")
      .displayName("Header")
      .description("Whether the csv file has a header")
      .defaultValue("false")
      .allowableValues(Set("true","false"))
      .required(true)
      .example("true")
    descriptor = header :: descriptor

    val delimiter = new PropertyDescriptor()
      .name("delimiter")
      .displayName("Delimiter")
      .description("The delimiter of csv file")
      .defaultValue("")
      .required(true)
      .example(",")
    descriptor = delimiter :: descriptor

    val schema = new PropertyDescriptor()
      .name("schema")
      .displayName("Schema")
      .description("The schema of csv file")
      .defaultValue("")
      .required(false)
      .example("id,name,gender,age")
    descriptor = schema :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/csv/CsvParser.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.CsvGroup)
  }

}

