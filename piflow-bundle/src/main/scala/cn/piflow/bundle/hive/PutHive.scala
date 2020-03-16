package cn.piflow.bundle.hive

import cn.piflow._
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.sql.{SaveMode, SparkSession}

class PutHive extends ConfigurableStop {

  val authorEmail: String = "xjzhu@cnic.cn"
  val description: String = "Save data to hive by overwrite mode"
  val inportList: List[String] = List(Port.DefaultPort.toString)
  val outportList: List[String] = List(Port.NonePort.toString)

  var database:String = _
  var table:String = _
  var saveFormat:String = _
  var saveMode:String = _


  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val inDF = in.read()

    inDF.write.format("hive").mode(saveMode).saveAsTable(database + "." + table)
    //inDF.show()
    //out.write(studentDF)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  def setProperties(map : Map[String, Any]) = {
    database = MapUtil.get(map,"database").asInstanceOf[String]
    table = MapUtil.get(map,"table").asInstanceOf[String]
    //saveFormat = MapUtil.get(map,"saveFormat").asInstanceOf[String]
    saveMode = MapUtil.get(map,"saveMode").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {

    val saveModeOption = Set("append","overwrite","error","ignore")
    val saveFormatOption = Set("parquet","orc","avro","csv","hive")
    var descriptor : List[PropertyDescriptor] = List()
    val database=new PropertyDescriptor().name("database").displayName("DataBase").description("The database name").defaultValue("").required(true)
    val table = new PropertyDescriptor().name("table").displayName("Table").description("The table name").defaultValue("").required(true)
    val saveMode = new PropertyDescriptor().name("saveMode").displayName("SaveMode").description("The save mode for table").allowableValues(saveModeOption).defaultValue("ignore").required(true)
    //val saveFormat = new PropertyDescriptor().name("saveFormat").displayName("saveFormat").description("The save format for table").allowableValues(saveFormatOption).defaultValue("csv").required(true)
    descriptor = database :: descriptor
    descriptor = table :: descriptor
    //descriptor = saveFormat :: descriptor
    descriptor = saveMode :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/hive/PutHiveStreaming.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.HiveGroup.toString)
  }


}
