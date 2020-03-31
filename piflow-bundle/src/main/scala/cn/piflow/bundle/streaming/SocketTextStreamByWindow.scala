package cn.piflow.bundle.streaming

import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.streaming.{Seconds, StreamingContext}
import org.apache.spark.streaming.dstream.DStream

class SocketTextStreamByWindow extends ConfigurableStreamingStop {
  override val authorEmail: String = "xjzhu@cnic.cn"
  override val description: String = "Receive text data from socket by window"
  override val inportList: List[String] = List(Port.DefaultPort)
  override val outportList: List[String] = List(Port.DefaultPort)
  override var batchDuration: Int = _

  var hostname:String =_
  var port:String=_
  var windowDuration:Int = _
  var slideDuration:Int = _

  override def setProperties(map: Map[String, Any]): Unit = {
    hostname=MapUtil.get(map,key="hostname").asInstanceOf[String]
    port=MapUtil.get(map,key="port").asInstanceOf[String]
    windowDuration=MapUtil.get(map,key="windowDuration").asInstanceOf[String].toInt
    slideDuration=MapUtil.get(map,key="slideDuration").asInstanceOf[String].toInt
    val timing = MapUtil.get(map,key="batchDuration")
    batchDuration=if(timing == None) new Integer(1) else timing.asInstanceOf[String].toInt
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val hostname = new PropertyDescriptor().name("hostname").displayName("hostname").description("Hostname to connect to for receiving data ").defaultValue("").required(true)
    val port = new PropertyDescriptor().name("port").displayName("port").description("Port to connect to for receiving data").defaultValue("").required(true)
    val batchDuration = new PropertyDescriptor().name("batchDuration").displayName("batchDuration").description("the streaming batch duration").defaultValue("1").required(true)
    val windowDuration = new PropertyDescriptor().name("windowDuration").displayName("windowDuration").description("the window duration, the unit is seconds").defaultValue("").required(true)
    val slideDuration = new PropertyDescriptor().name("slideDuration").displayName("slideDuration").description("the slide duration, the unit is seconds").defaultValue("").required(true)
    descriptor = hostname :: descriptor
    descriptor = port :: descriptor
    descriptor = batchDuration :: descriptor
    descriptor = windowDuration :: descriptor
    descriptor = slideDuration :: descriptor
    descriptor
  }

  //TODO: change icon
  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/streaming/SocketTextStreamByWindow.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.StreamingGroup)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {


  }

  override def getDStream(ssc: StreamingContext): DStream[String] = {
    val dstream = ssc.socketTextStream(hostname,Integer.parseInt(port))
    dstream.window(Seconds(windowDuration),Seconds(slideDuration))
    //dstream.reduceByWindow(_ + _,Seconds(windowDuration),Seconds(slideDuration))
  }

}
