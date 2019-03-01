package cn.piflow.bundle.streaming

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStreamingStop, PortEnum, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.storage.StorageLevel
import org.apache.spark.streaming.StreamingContext
import org.apache.spark.streaming.dstream.DStream
import org.apache.spark.streaming.flume._

class FlumeStream extends ConfigurableStreamingStop{
  override val timing: Integer = 10
  override val authorEmail: String = "xjzhu@cnic.cn"
  override val description: String = "get data from flume Stream."
  override val inportList: List[String] = List(PortEnum.NonePort)
  override val outportList: List[String] = List(PortEnum.DefaultPort)

  var hostname:String =_
  var port:Int=_

  override def setProperties(map: Map[String, Any]): Unit = {
    hostname=MapUtil.get(map,key="hostname").asInstanceOf[String]
    port=MapUtil.get(map,key="port").asInstanceOf[String].toInt
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val hostname = new PropertyDescriptor().name("hostname").displayName("hostname").description("flume sink hostname ").defaultValue("").required(true)
    val port = new PropertyDescriptor().name("port").displayName("port").description("flume sink port").defaultValue("").required(true)
    descriptor = hostname :: descriptor
    descriptor = port :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("mllib.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.StreamingGroup)
  }

  override def getDStream(ssc: StreamingContext): DStream[String] = {
    val flumeStream = FlumeUtils.createStream(ssc, hostname, port)
    flumeStream.map(e => new String(e.event.getBody.array(), "UTF-8"))
  }

  override def initialize(ctx: ProcessContext): Unit = {}

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {}
}
