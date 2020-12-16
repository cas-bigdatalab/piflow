package cn.piflow.bundle.visualization

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableVisualizationStop, Port, StopGroup, VisualizationType}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.sql.SparkSession

class TableShow extends ConfigurableVisualizationStop{
  override var visualizationType: String = VisualizationType.Table
  override val authorEmail: String = "xjzhu@cnic.cn"
  override val description: String = "Show data with table"
  override val inportList: List[String] = List(Port.DefaultPort)
  override val outportList: List[String] = List(Port.DefaultPort)

  var showField:String =_

  override def setProperties(map: Map[String, Any]): Unit = {
    showField=MapUtil.get(map,key="showField").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val showField = new PropertyDescriptor()
      .name("showField")
      .displayName("ShowField")
      .description("The fields  of data to show.")
      .defaultValue("*")
      .example("id,name,age")
      .required(true)

    descriptor = showField :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/visualization/table.png")
  }

  override def getGroup(): List[String] = {
    List{StopGroup.Visualization}
  }

  override def initialize(ctx: ProcessContext): Unit = {}

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val sqlContext=spark.sqlContext
    val dataFrame = in.read()
    dataFrame.createOrReplaceTempView("TableShow")
    val sqlText = "select " + showField+ " from TableShow"
    println("TableShow Sql: " + sqlText)
    val tableShowDF = spark.sql(sqlText)
    out.write(tableShowDF.repartition(1))

  }
}
