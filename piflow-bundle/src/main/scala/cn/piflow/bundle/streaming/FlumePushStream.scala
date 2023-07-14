//package cn.piflow.bundle.streaming
//
//import cn.piflow.conf.bean.PropertyDescriptor
//import cn.piflow.conf.util.{ImageUtil, MapUtil}
//import cn.piflow.conf.{ConfigurableStreamingStop, Port, StopGroup}
//import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
//import org.apache.spark.streaming.StreamingContext
//import org.apache.spark.streaming.dstream.DStream
//import org.apache.spark.streaming.flume._
//
//class FlumePushStream extends ConfigurableStreamingStop{
//  override var batchDuration: Int = _
//  override val authorEmail: String = "xjzhu@cnic.cn"
//  override val description: String = "Flume pushes the message to spark streaming"
//  override val inportList: List[String] = List(Port.DefaultPort)
//  override val outportList: List[String] = List(Port.DefaultPort)
//
//  var hostname:String =_
//  var port:Int=_
//
//  override def setProperties(map: Map[String, Any]): Unit = {
//    hostname=MapUtil.get(map,key="hostname").asInstanceOf[String]
//    port=MapUtil.get(map,key="port").asInstanceOf[String].toInt
//    val timing = MapUtil.get(map,key="batchDuration")
//    batchDuration=if(timing == None) new Integer(1) else timing.asInstanceOf[String].toInt
//  }
//
//  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
//    var descriptor : List[PropertyDescriptor] = List()
//    val hostname = new PropertyDescriptor().name("hostname").displayName("hostname")
//      .description("hostname of the slave machine to which the flume data will be sent, the hostName must be one of the cluster worker node")
//      .defaultValue("0.0.0.0")
//      .example("0.0.0.0")
//      .required(true)
//    val port = new PropertyDescriptor().name("port").displayName("port")
//      .description("Port of the slave machine to which the flume data will be sent, the port should be greater than 10000")
//      .defaultValue("")
//      .example("6666").required(true)
//    val batchDuration = new PropertyDescriptor().name("batchDuration").displayName("batchDuration").description("the streaming batch duration")
//      .defaultValue("5")
//      .example("5").required(true)
//    descriptor = hostname :: descriptor
//    descriptor = port :: descriptor
//    descriptor = batchDuration :: descriptor
//    descriptor
//  }
//
//  override def getIcon(): Array[Byte] = {
//    ImageUtil.getImage("icon/streaming/FlumeStream.png")
//  }
//
//  override def getGroup(): List[String] = {
//    List(StopGroup.StreamingGroup)
//  }
//
//  override def getDStream(ssc: StreamingContext): DStream[String] = {
//    val flumeStream = FlumeUtils.createStream(ssc, hostname, port)
//    flumeStream.map(e => new String(e.event.getBody.array(), "UTF-8"))
//  }
//
//  override def initialize(ctx: ProcessContext): Unit = {}
//
//  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {}
//}
