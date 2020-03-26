package cn.piflow.bundle.file

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf._
import org.apache.spark.sql.SparkSession

class RegexTextProcess extends ConfigurableStop{
    val authorEmail: String = "06whuxx@163.com"
    val description: String = "Replace values in a column with regex"
    val inportList: List[String] = List(Port.DefaultPort)
    val outportList: List[String] = List(Port.DefaultPort)

    var regex:String =_
    var columnName:String=_
    var replaceStr:String=_

    def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
      val spark = pec.get[SparkSession]()
      val sqlContext=spark.sqlContext
      val dfOld = in.read()
      val regexText=regex
      val replaceText=replaceStr
      dfOld.createOrReplaceTempView("thesis")
      sqlContext.udf.register("regexPro",(str:String)=>str.replaceAll(regexText,replaceText))
      val sqlText:String="select *,regexPro("+columnName+") as "+columnName+"_new from thesis"
      val dfNew=sqlContext.sql(sqlText)
      out.write(dfNew)
    }

  def initialize(ctx: ProcessContext): Unit = {

  }


  def setProperties(map: Map[String, Any]): Unit = {
    regex=MapUtil.get(map,key="regex").asInstanceOf[String]
    columnName=MapUtil.get(map,key="columnName").asInstanceOf[String]
    replaceStr=MapUtil.get(map,key="replaceStr").asInstanceOf[String]

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val regex = new PropertyDescriptor()
      .name("regex")
      .displayName("Regex")
      .description("regex")
      .defaultValue("")
      .required(true)
      .example("0001")
    descriptor = regex :: descriptor

    val columnName = new PropertyDescriptor()
      .name("columnName")
      .displayName("ColumnName")
      .description("The columns you want to replace")
      .defaultValue("")
      .required(true)
      .example("id")
    descriptor = columnName :: descriptor

    val replaceStr = new PropertyDescriptor()
      .name("replaceStr")
      .displayName("ReplaceStr")
      .description("Value after replacement")
      .defaultValue("")
      .required(true)
      .example("1111")
    descriptor = replaceStr :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/file/RegexTextProcess.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.FileGroup)
  }
}
