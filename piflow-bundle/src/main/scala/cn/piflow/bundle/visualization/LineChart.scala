package cn.piflow.bundle.visualization

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableVisualizationStop, Port, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.sql.SparkSession

class LineChart extends ConfigurableVisualizationStop{
  override val authorEmail: String = "xjzhu@cnic.cn"
  override val description: String = "Show data with line chart. " +
    "X represents the abscissa, the ordinate is represented by customizedProperties, " +
    "the key is the dimentsion, and the value is the operation for the dimentsion, such as SUM."
  override val inportList: List[String] = List(Port.DefaultPort)
  override val outportList: List[String] = List(Port.DefaultPort)

  var x:String =_
  //var dimension:String =_

  override val isCustomized: Boolean = true
  override val customizedAllowValue: List[String] = List("COUNT","SUM","AVG","MAX","MIN")

  override def setProperties(map: Map[String, Any]): Unit = {
    x=MapUtil.get(map,key="x").asInstanceOf[String]
    //dimension=MapUtil.get(map,key="dimension").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val abscissa = new PropertyDescriptor()
      .name("x")
      .displayName("x")
      .description("The abscissa  of line chart")
      .defaultValue("")
      .required(true)
    /*val dimension = new PropertyDescriptor()
      .name("dimension")
      .displayName("Dimension")
      .description("The dimension of line chart, multi demensions are separated by commas")
      .defaultValue("")
      .required(true)*/
    descriptor = abscissa :: descriptor
    //descriptor = dimension :: descriptor
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

    if(this.customizedProperties != null || this.customizedProperties.size != 0){

      println("dimension is " + this.customizedProperties.keySet.mkString(",") + "!!!!!!!!!!!!!!!")

      var dimensionActionArray = List[String]()
      val it = this.customizedProperties.keySet.iterator
      while (it.hasNext){
        val dimention = it.next()
        val action = MapUtil.get(this.customizedProperties,dimention).asInstanceOf[String]
        val dimentionAction = action + "(" + dimention + ") as " + dimention + "_" + action
        dimensionActionArray = dimensionActionArray :+ dimentionAction
      }

      val sqlText = "select " + x + "," + dimensionActionArray.mkString(",") + " from LineChart group by " + x;
      println("LineChart Sql: " + sqlText)
      val lineChartDF = spark.sql(sqlText)
      out.write(lineChartDF.repartition(1))
    }else{
      out.write(dataFrame)
    }
  }
}
