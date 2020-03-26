package cn.piflow.bundle.common

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.DataFrame

class Distinct extends ConfigurableStop{
  override val authorEmail: String = "yangqidong@cnic.cn"
  override val description: String = "Duplicate based on the specified column name or all colume names"
  override val inportList: List[String] =List(Port.DefaultPort)
  override val outportList: List[String] = List(Port.DefaultPort)

  var columnNames:String=_

  override def setProperties(map: Map[String, Any]): Unit = {
    columnNames = MapUtil.get(map,"columnNames").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val fields = new PropertyDescriptor()
      .name("columnNames")
      .displayName("ColumnNames")
      .description("Fill in the column names you want to duplicate,multiple columns names separated by commas,if not,all the columns will be deduplicated")
      .defaultValue("")
      .required(false)
      .example("id")
    descriptor = fields :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/common/Distinct.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.CommonGroup)
  }


  override def initialize(ctx: ProcessContext): Unit = {

  }

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val inDf: DataFrame = in.read()
    var outDf: DataFrame = null
    if(columnNames.length > 0){
      val fileArr: Array[String] = columnNames.split(",")
      outDf = inDf.dropDuplicates(fileArr)
    }else{
      outDf = inDf.distinct()
    }
    out.write(outDf)
  }
}
