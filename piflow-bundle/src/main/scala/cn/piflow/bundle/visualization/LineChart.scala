package cn.piflow.bundle.visualization

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableVisualizationStop, Port, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.sql.SparkSession

class LineChart extends ConfigurableVisualizationStop{
  override val authorEmail: String = "xjzhu@cnic.cn"
  override val description: String = "show data with line chart"
  override val inportList: List[String] = List(Port.DefaultPort)
  override val outportList: List[String] = List(Port.DefaultPort)

  var abscissa:String =_
  var dimension:String =_

  override def setProperties(map: Map[String, Any]): Unit = {
    abscissa=MapUtil.get(map,key="abscissa").asInstanceOf[String]
    dimension=MapUtil.get(map,key="dimension").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val abscissa = new PropertyDescriptor()
      .name("abscissa")
      .displayName("Abscissa")
      .description("The abscissa x of line chart")
      .defaultValue("")
      .required(true)
    val dimension = new PropertyDescriptor()
      .name("dimension")
      .displayName("Dimension")
      .description("The dimension of line chart, multi demensions are separated by commas")
      .defaultValue("")
      .required(true)
    descriptor = abscissa :: descriptor
    descriptor = dimension :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/visualization/line-chart.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.Visualization)
  }

  override def initialize(ctx: ProcessContext): Unit = {}

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val sqlContext=spark.sqlContext
    val dataFrame = in.read()
    dataFrame.createOrReplaceTempView("LineChart")

    println("dimension is " + dimension + "!!!!!!!!!!!!!!!")
    val dimensionArray = dimension.split(",")
    var dimensionCountArray = List[String]()
    dimensionArray.map(d => {
      val dCount = "count(" + d + ") as " + d + "_count"
      dimensionCountArray = dimensionCountArray :+ dCount
    })
    val sqlText = "select " + abscissa + "," + dimensionCountArray.mkString(",") + " from LineChart group by " + abscissa;
    println("LineChart Sql: " + sqlText)
    val lineChartDF = spark.sql(sqlText)
    out.write(lineChartDF)
  }
}
