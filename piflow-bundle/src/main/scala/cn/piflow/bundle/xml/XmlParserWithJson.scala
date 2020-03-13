package cn.piflow.bundle.xml

import cn.piflow._
import cn.piflow.bundle.util.XmlToJson
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.rdd.RDD
import org.apache.spark.sql.{DataFrame, SparkSession}


class XmlParserWithJson extends ConfigurableStop {

  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "Parse xml fields "
  val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)

  var xmlColumns:String = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val spark = pec.get[SparkSession]()

    val df = in.read()

    spark.sqlContext.udf.register("xmlToJson",(str:String)=>{
      XmlToJson.xmlParse(str.replaceAll("\n","\t"))
    })
    val columns: Array[String] = xmlColumns.toLowerCase.split(",")

    val fields: Array[String] = df.schema.fieldNames
    var fieldString = new StringBuilder
    fields.foreach(x=>{
      if (columns.contains(x.toLowerCase)){
        fieldString.append(s"xmlToJson(${x}) as ${x} ,")
      } else {
        fieldString.append(s"${x},")
      }
    })

    df.createOrReplaceTempView("temp")
    val sqlText = "select " +fieldString.stripSuffix(",")+ " from temp"
    val frame: DataFrame = spark.sql(sqlText)

    val rdd: RDD[String] = frame.toJSON.rdd.map(x => {
      x.toString().replace("\\n", "").replace("}\"", "}").replace(":\"{", ":{").replace("\\","")
    })

    val outDF: DataFrame = spark.read.json(rdd)
    outDF.printSchema()

    out.write(outDF)

  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  def setProperties(map : Map[String, Any]) = {
    xmlColumns = MapUtil.get(map,"xmlColumns").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val xmlColumns = new PropertyDescriptor().name("xmlColumns").displayName("xmlColumns").description("you want to parse contains XML fields ,Multiple are separated by commas").defaultValue("").required(true)
    descriptor = xmlColumns :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/xml/XmlParser.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.XmlGroup.toString)
  }



}
