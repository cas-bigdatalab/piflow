package cn.piflow.bundle.streaming

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStreamingStop, PortEnum, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.streaming.StreamingContext
import org.apache.spark.streaming.dstream.DStream

class TextFileStream extends ConfigurableStreamingStop{
  override val timing: Integer = 1
  override val authorEmail: String = "xjzhu@cnic.cn"
  override val description: String = "get text file streaming data"
  override val inportList: List[String] = List(PortEnum.NonePort.toString)
  override val outportList: List[String] = List(PortEnum.DefaultPort.toString)

  var directory:String =_

  override def setProperties(map: Map[String, Any]): Unit = {
    directory=MapUtil.get(map,key="directory").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val directory = new PropertyDescriptor().name("directory").displayName("directory").description("the directory of files ").defaultValue("").required(true)
    descriptor = directory :: descriptor
    descriptor
  }

  //TODO: change icon
  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/streaming/textFileStream.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.StreamingGroup)
  }

  override def getDStream(ssc: StreamingContext): DStream[String] = {
    val dstream = ssc.textFileStream(directory)
    dstream
  }

  override def initialize(ctx: ProcessContext): Unit = {}

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {}
}
