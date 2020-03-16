package cn.piflow.bundle.clean

import java.beans.Transient

import cn.piflow.bundle.util.CleanUtil
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.sql.SparkSession
import org.apache.spark.sql.types.StructField

class EmailClean extends ConfigurableStop{
  val authorEmail: String = "songdongze@cnic.cn"
  val description: String = "Clean email format data."
  val inportList: List[String] = List(Port.DefaultPort.toString)
  val outportList: List[String] = List(Port.DefaultPort.toString)

  var columnName:String=_

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val sqlContext=spark.sqlContext
    val dfOld = in.read()
    dfOld.createOrReplaceTempView("thesis")
    sqlContext.udf.register("regexPro",(str:String)=>CleanUtil.processEmail(str))
    val structFields: Array[String] = dfOld.schema.fieldNames
    val columnNames = columnName.split(",").toSet
    val sqlNewFieldStr = new StringBuilder
    columnNames.foreach(c=>{
      if (columnNames.contains(c)) {
        sqlNewFieldStr ++= ",regexPro("
        sqlNewFieldStr ++= c
        sqlNewFieldStr ++= ") as "
        sqlNewFieldStr ++= c
        sqlNewFieldStr ++= "_new "
      }
    })

    val sqlText:String="select * " + sqlNewFieldStr + " from thesis"

    val dfNew=sqlContext.sql(sqlText)
    dfNew.createOrReplaceTempView("thesis")
    val schemaStr = new StringBuilder
    structFields.foreach(field => {
      schemaStr ++= field
      if (columnNames.contains(field)) {
        schemaStr ++= "_new as "
        schemaStr ++= field
      }
      schemaStr ++= ","
    })
    val sqlText1:String = "select " + schemaStr.substring(0,schemaStr.length -1) + " from thesis"
    val dfNew1=sqlContext.sql(sqlText1)

    //dfNew.show()
    out.write(dfNew1)
  }


  def initialize(ctx: ProcessContext): Unit = {

  }


  def setProperties(map: Map[String, Any]): Unit = {
    columnName=MapUtil.get(map,key="columnName").asInstanceOf[String]

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val columnName = new PropertyDescriptor().name("columnName").displayName("COLUMN_NAME").description("The columnName you want to clean,Multiple are separated by commas").defaultValue("").required(true)
    descriptor = columnName :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/clean/EmailClean.png")

  }

  override def getGroup(): List[String] = {
    List(StopGroup.CleanGroup.toString)
  }

}
