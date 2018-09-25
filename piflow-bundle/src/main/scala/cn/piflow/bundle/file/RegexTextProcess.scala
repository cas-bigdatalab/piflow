package cn.piflow.bundle.file

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.MapUtil
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, FileGroup, StopGroup, StopGroupEnum}
import org.apache.spark.sql.SparkSession



class RegexTextProcess extends ConfigurableStop{
    override val authorEmail: String = "xiaoxiao@cnic.cn"
    val inportCount: Int = 0
    val outportCount: Int = 1
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
      dfNew.show()
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
    val regex = new PropertyDescriptor().name("regex").displayName("REGEX").defaultValue("").required(true)
    val columnName = new PropertyDescriptor().name("columnName").displayName("COLUMN_NAME").defaultValue("").required(true)
    val replaceStr = new PropertyDescriptor().name("replaceStr").displayName("REPLACE_STR").defaultValue("").required(true)
    descriptor = regex :: descriptor
    descriptor = columnName :: descriptor
    descriptor = replaceStr :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = ???

  override def getGroup(): List[String] = {
    List(StopGroupEnum.FileGroup.toString)
  }
}
