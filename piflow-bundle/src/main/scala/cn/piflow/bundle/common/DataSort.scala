package cn.piflow.bundle.common

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.SparkSession
import org.apache.spark.sql.functions.col

class DataSort extends ConfigurableStop{
  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "数据排序"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] =  List(Port.DefaultPort)

  var sortField: String = _
  var sortOrder:String = _

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    var dataSortDF = in.read()

    val cols: Seq[String] = Seq(sortField.split(","): _*)

    if(sortOrder.equals("asc")){
      dataSortDF  =  dataSortDF.repartition(1).orderBy(cols.map(col).map(_.asc): _*)
    } else {
      dataSortDF  =  dataSortDF.repartition(1).orderBy(cols.map(col).map(_.desc): _*)
    }

    out.write(dataSortDF)

  }

  override def setProperties(map: Map[String, Any]): Unit = {
    sortField = MapUtil.get(map,"sortField").asInstanceOf[String]
    sortOrder = MapUtil.get(map,"sortOrder").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val sortField = new PropertyDescriptor()
      .name("sortField")
      .displayName("sortField")
      .description("排序字段")
      .defaultValue("")
      .required(true)
      .example("id")
    descriptor = sortField :: descriptor

    val sortOrder = new PropertyDescriptor()
      .name("sortOrder")
      .displayName("sortOrder")
      .description("排序方式：默认升序")
      .defaultValue("asc")
      .allowableValues(Set("asc","desc"))
      .required(true)
      .example("asc")

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/csv/CsvParser.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.CommonGroup)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

}
