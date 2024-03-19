package cn.piflow.bundle.visualization

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableVisualizationStop, Port, StopGroup}
import cn.piflow.util.PropertyUtil
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.{SaveMode, SparkSession}

import java.util.Properties

class VisualDisplay extends ConfigurableVisualizationStop  {
  override val authorEmail: String = "ygang@cnic.cn"
  override val description: String = "Data visualization display"
  override val inportList: List[String] = List(Port.DefaultPort)
  override val outportList: List[String] = List(Port.DefaultPort)

  override var visualizationType: String = "VisualDisplay"

  var X_axis:String = _
  var Y_axis:String = _
  var visTableName:String = _

  override def setProperties(map: Map[String, Any]): Unit = {
    X_axis=MapUtil.get(map,key="X_axis").asInstanceOf[String]
    Y_axis=MapUtil.get(map,key="Y_axis").asInstanceOf[String]
    visTableName=MapUtil.get(map,key="visTableName").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val X_axis = new PropertyDescriptor()
      .name("X_axis")
      .displayName("X_axis")
      .description("X轴坐标")
      .defaultValue("")
      .example("")
      .required(true)

    descriptor = X_axis :: descriptor

    val Y_axis = new PropertyDescriptor()
      .name("Y_axis")
      .displayName("Y_axis")
      .description("Y轴坐标")
      .defaultValue("")
      .example("")
      .required(true)
    descriptor = Y_axis :: descriptor

    val visTableName = new PropertyDescriptor()
      .name("visTableName")
      .displayName("visTableName")
      .description("数据临时存储表")
      .defaultValue("")
      .example("")
      .required(true)
    descriptor = visTableName :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/visualization/vis.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.Visualization)
  }

  override def initialize(ctx: ProcessContext): Unit = {}

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val user = PropertyUtil.getPropertyValue("vis.mysql.user")
    val password = PropertyUtil.getPropertyValue("vis.mysql.password")
    val url = PropertyUtil.getPropertyValue("vis.mysql.url")

    println(user+"\n"+password+"\n"+url)

    val jdbcDF = in.read()
    val properties = new Properties()
    properties.put("user", user)
    properties.put("password", password)
    jdbcDF.write.mode(SaveMode.Overwrite).jdbc(url,visTableName,properties)

  }
}
