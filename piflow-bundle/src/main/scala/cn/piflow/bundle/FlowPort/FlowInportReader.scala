package cn.piflow.bundle.FlowPort

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port}
import cn.piflow.util.HdfsUtil
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.SparkSession

class FlowInportReader extends ConfigurableStop {
  override val authorEmail: String = "xjzhu@cnic.cn"
  override val description: String = "inport for flow."
  override val inportList: List[String] = List(Port.DefaultPort)
  override val outportList: List[String] = List(Port.DefaultPort)


  var dataSource: String = _

  override def setProperties(map: Map[String, Any]): Unit = {
    dataSource = MapUtil.get(map,key="dataSource").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = { List()}

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/hdfs/GetHdfs.png")
  }

  override def getGroup(): List[String] = {
    List()
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val spark = pec.get[SparkSession]()
    val sc= spark.sparkContext
    import spark.implicits._

    val df = spark.read.json(dataSource)
    df.schema.printTreeString()
    out.write(df)
  }
}
