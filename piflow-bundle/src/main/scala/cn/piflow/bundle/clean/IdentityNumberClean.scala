package cn.piflow.bundle.clean

import java.text.SimpleDateFormat
import java.util.regex.Pattern
import java.util.{Calendar, Date}

import cn.piflow.bundle.util.CleanUtil
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.sql.SparkSession

import scala.reflect.macros.ParseException

class IdentityNumberClean extends ConfigurableStop{
  val authorEmail: String = "06whuxx@163.com"
  val description: String = "Clean Id Card data."
  val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)
  //var regex:String =_
  var columnName:String=_
  //var replaceStr:String=_

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val sqlContext=spark.sqlContext
    val dfOld = in.read()
    dfOld.createOrReplaceTempView("thesis")
    sqlContext.udf.register("regexPro",(str:String)=>CleanUtil.processCardCode(str))
    val sqlText:String="select *,regexPro("+columnName+") as "+columnName+"_new from thesis"
    val dfNew=sqlContext.sql(sqlText)
    dfNew.show()
    out.write(dfNew)
  }


  def initialize(ctx: ProcessContext): Unit = {

  }


  def setProperties(map: Map[String, Any]): Unit = {
    columnName=MapUtil.get(map,key="columnName").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val columnName = new PropertyDescriptor().name("columnName").displayName("COLUMN_NAME").defaultValue("").required(true)
    descriptor = columnName :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("clean.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.CleanGroup.toString)
  }
}
