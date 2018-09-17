package cn.piflow.bundle.clean

import cn.piflow.bundle.util.CleanUtil
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{CleanGroup, ConfigurableStop, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.MapUtil
import org.apache.spark.sql.SparkSession

class TitleClean extends ConfigurableStop{
  override val authorEmail: String = "xiaoxiao@cnic.cn"
  val inportCount: Int = 0
  val outportCount: Int = 1
  var columnName:String=_

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val sqlContext=spark.sqlContext
    val dfOld = in.read()
    dfOld.createOrReplaceTempView("thesis")
    sqlContext.udf.register("regexPro",(str:String)=>CleanUtil.processTitle(str))
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

  override def getIcon(): Array[Byte] = ???

  override def getGroup(): StopGroup = {
    CleanGroup
  }

}
