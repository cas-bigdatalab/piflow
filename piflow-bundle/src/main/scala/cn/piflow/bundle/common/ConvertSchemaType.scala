package cn.piflow.bundle.common

import cn.piflow._
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.sql.{DataFrame, SparkSession}
import org.apache.spark.sql.types._

import scala.collection.mutable.ArrayBuffer


class ConvertSchemaType extends ConfigurableStop {

  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "Transform the schema dataType"
  val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)


  var stringType:String = _
  var integerType:String = _
  var all:String = _


  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    var df = in.read()
    var colName = ArrayBuffer[String]()
    var outDf :DataFrame= df


    if (all.equals("true")){
      colName.clear()
    df.schema.foreach(x=>{
      colName += x.name
    })
      import org.apache.spark.sql.functions._

      colName.foreach(name => {
        outDf = outDf.withColumn(name, col(name).cast(StringType))
      })

    } else {
      if (stringType.nonEmpty){
        colName.clear()
        stringType.split(",").foreach(x=>{
          colName += x
        })

        import org.apache.spark.sql.functions._

        colName.foreach(name => {
          outDf = outDf.withColumn(name, col(name).cast(StringType))
        })

      }
      if (integerType.nonEmpty){
        colName.clear()
        integerType.split(",").foreach(x=>{
          colName += x
        })

        import org.apache.spark.sql.functions._

        colName.foreach(name => {
          outDf = outDf.withColumn(name, col(name).cast(IntegerType))
        })

      }
    }



    out.write(outDf)

  }

  def initialize(ctx: ProcessContext): Unit = {

  }


  def setProperties(map : Map[String, Any]): Unit = {
    stringType = MapUtil.get(map,"stringType").asInstanceOf[String]
    integerType = MapUtil.get(map,"integerType").asInstanceOf[String]
    all = MapUtil.get(map,"all").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val all = new PropertyDescriptor().name("all").displayName("all").description("if true ,the schema all types are converted to stringType").defaultValue("true").required(true)
    val stringType = new PropertyDescriptor().name("stringType").displayName("stringType").description("the specified field types are converted to stringType, Multiple are separated by commas").defaultValue("").required(true)
    val integerType = new PropertyDescriptor().name("integerType").displayName("integerType").description("the specified types are converted to integerType, Multiple are separated by commas").defaultValue("").required(true)


    descriptor = stringType :: descriptor
    descriptor = integerType :: descriptor
    descriptor = all :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/common/ConvertSchema.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.CommonGroup.toString)
  }

}



