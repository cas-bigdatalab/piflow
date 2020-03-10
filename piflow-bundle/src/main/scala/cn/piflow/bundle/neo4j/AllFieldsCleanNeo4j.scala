package cn.piflow.bundle.neo4j

import cn.piflow.bundle.util.CleanUtil
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.{DataFrame, Row, SparkSession}
import org.apache.spark.sql.types.StringType

import scala.collection.mutable.ListBuffer

class AllFieldsCleanNeo4j extends ConfigurableStop {
  val authorEmail: String = "anhong12@cnic.cn"
  val description: String = "Clean DataFrame for NSFC Neo4j"

  val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)


//
//  var regex:String=_
//  var replaceStr:String=_

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()

    val df = in.read()
    df.createOrReplaceTempView("temp")

    // clean authors
    spark.sqlContext.udf.register("cleanFields", (fieldStr: String) => {
      if (fieldStr == null) null
      else fieldStr.replaceAll("\"", "")
    })


    val fieldNames: Array[String] = df.schema.fieldNames
    val sqlStringBuilder = new StringBuilder
    for (i <- 0 until fieldNames.length) {
      sqlStringBuilder.append("cleanFields(" + fieldNames(i) + ") as "+fieldNames(i) +",")
    }

    val sqlString = sqlStringBuilder.dropRight(1).toString()

    val frame: DataFrame = spark.sql("select   "+sqlString +"   from temp")


    //dfNew.show()
    out.write(frame)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }


  def setProperties(map: Map[String, Any]): Unit = {
//    regex=MapUtil.get(map,key="regex").asInstanceOf[String]
//    replaceStr=MapUtil.get(map,key="replaceStr").asInstanceOf[String]

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
//
//    val regex = new PropertyDescriptor().name("regex").displayName("regex").description("the regex which to be repalced").defaultValue("\"").required(true)
//    val replaceStr = new PropertyDescriptor().name("repalceStr").displayName("replaceStr").description("repalace what").defaultValue("").required(true)
//    descriptor = regex :: descriptor
//    descriptor = replaceStr :: descriptor





    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/clean/TitleClean.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.Neo4jGroup.toString)
  }

}
