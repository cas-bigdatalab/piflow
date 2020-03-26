package cn.piflow.bundle.clean

import cn.piflow.bundle.util.CleanUtil
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.sql.SparkSession
import org.apache.spark.sql.types.StructField

class TitleClean extends ConfigurableStop{
  val authorEmail: String = "06whuxx@163.com"
  val description: String = "Cleaning title data"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var columnName:String=_

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val sqlContext=spark.sqlContext
    val dfOld = in.read()
    dfOld.createOrReplaceTempView("thesis")
    sqlContext.udf.register("regexPro",(str:String)=>CleanUtil.processTitle(str))
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
    val sqlTextNew:String = "select " + schemaStr.substring(0,schemaStr.length -1) + " from thesis"
    val dfNew1=sqlContext.sql(sqlTextNew)

    out.write(dfNew1)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }


  def setProperties(map: Map[String, Any]): Unit = {
    columnName=MapUtil.get(map,key="columnName").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val columnName = new PropertyDescriptor()
      .name("columnName")
      .displayName("Column_Name")
      .description("Column names are what you want to clean,multiple column names are separated by commas")
      .defaultValue("")
      .required(true)
      .example("title")
    descriptor = columnName :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/clean/TitleClean.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.CleanGroup)
  }

}
