package cn.piflow.bundle.json

import cn.piflow._
import cn.piflow.bundle.util.JsonUtil
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.sql.{DataFrame, SparkSession}

class JsonParser extends ConfigurableStop{

  val authorEmail: String = "xjzhu@cnic.cn"
  val description: String = "Parse json file"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var jsonPath: String = _
  var tag : String = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val spark = pec.get[SparkSession]()

    val jsonPathARR: Array[String] = jsonPath.split(",").map(x => x.trim)

    var FinalDF = spark.read.option("multiline","true").json(jsonPathARR(0))

    if(jsonPathARR.length>1){
      for(x<-(1 until jsonPathARR.length)){
        var jDF: DataFrame = spark.read.option("multiline","true").json(jsonPathARR(x))
        val ff: DataFrame = FinalDF.union(jDF).toDF()
        FinalDF=ff
      }
    }
    FinalDF.printSchema()

    if(tag.length>0){
      val writeDF: DataFrame = JsonUtil.ParserJsonDF(FinalDF,tag)
      FinalDF=writeDF
    }

    out.write(FinalDF)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  override def setProperties(map: Map[String, Any]): Unit = {
    jsonPath = MapUtil.get(map,"jsonPath").asInstanceOf[String]
    tag = MapUtil.get(map,"tag").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val jsonPath = new PropertyDescriptor()
      .name("jsonPath")
      .displayName("jsonPath")
      .description("The path of the json file,Separate multiple files with commas")
      .defaultValue("")
      .required(true)
      .example("hdfs://master:9000/work/json/test/example.json,hdfs://master:9000/work/json/test/example1.json")

    val tag = new PropertyDescriptor()
      .name("tag")
      .displayName("Tag")
      .description("The tag you want to parse,If you want to open an array field,you have to write it like this:links_name(MasterField_ChildField)")
      .defaultValue("")
      .required(false)
      .example("name,province_name")

    descriptor = jsonPath :: descriptor
    descriptor = tag :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/json/jsonParser.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.JsonGroup)
  }

}

