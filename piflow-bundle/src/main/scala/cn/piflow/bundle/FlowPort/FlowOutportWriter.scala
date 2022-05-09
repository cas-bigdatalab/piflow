package cn.piflow.bundle.FlowPort

import java.text.SimpleDateFormat
import java.util.Date

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, Port}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.ImageUtil
import cn.piflow.util.{H2Util, HdfsUtil}
import org.apache.spark.sql.SparkSession

class FlowOutportWriter extends ConfigurableStop {
  override val authorEmail: String = "xjzhu@cnic.cn"
  override val description: String = "outport for flow."
  override val inportList: List[String] = List(Port.DefaultPort)
  override val outportList: List[String] = List(Port.DefaultPort)

  override def setProperties(map: Map[String, Any]): Unit = {}

  override def getPropertyDescriptor(): List[PropertyDescriptor] = { List()}

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/hdfs/PutHdfs.png")
  }

  override def getGroup(): List[String] = {
    List()
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val df = in.read()

    val spark = pec.get[SparkSession]()
    val appId = spark.sparkContext.applicationId
    val datacenterPath = pec.get("datacenter.path").asInstanceOf[String].stripSuffix("/") + "/" + appId  + "/" + pec.getStopJob().getStopName();
    df.write.json(datacenterPath)
    //init Accumulator
    var dataSize=spark.sparkContext.longAccumulator("dataSize")
    df.foreach(a=>{
      dataSize.add(a.toString().getBytes("UTF-8").length)
    })
    //wirte to h2
    val now: Date = new Date()
    val dateFormat: SimpleDateFormat = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss")
    val date = dateFormat.format(now)
    H2Util.addFlowDataSize(appId,dataSize.toString,date)
  }
}
