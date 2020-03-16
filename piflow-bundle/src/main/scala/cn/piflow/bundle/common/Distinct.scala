package cn.piflow.bundle.common

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.DataFrame

class Distinct extends ConfigurableStop{
  override val authorEmail: String = "yangqidong@cnic.cn"
  override val description: String = "Reduplicate data according to all fields or fields you specify"
  override val inportList: List[String] =List(Port.DefaultPort.toString)
  override val outportList: List[String] = List(Port.DefaultPort.toString)

  var files:String=_

  override def setProperties(map: Map[String, Any]): Unit = {
    files = MapUtil.get(map,"files").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val files = new PropertyDescriptor().name("files").displayName("files").description("To de-duplicate the field, you can fill in the field name, " +
      "if there are more than one, please use, separate. You can also not fill in, we will be based on all fields as a condition to weight.").defaultValue("").required(false)
    descriptor = files :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/common/Distinct.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.CommonGroup.toString)
  }


  override def initialize(ctx: ProcessContext): Unit = {

  }

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val inDf: DataFrame = in.read()
    var outDf: DataFrame = null
    if(files.length > 0){
      val fileArr: Array[String] = files.split(",")
      outDf = inDf.dropDuplicates(fileArr)
    }else{
      outDf = inDf.distinct()
    }
    out.write(outDf)
  }
}
