package cn.piflow.bundle.stream

import cn.piflow.bundle.util.SensorReading
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.flink.api.common.serialization.SimpleStringEncoder
import org.apache.flink.streaming.api.functions.sink.filesystem.StreamingFileSink
import org.apache.flink.streaming.api.scala.DataStream
import org.apache.flink.core.fs.Path

class FileSink extends ConfigurableStop{
  override val authorEmail: String = "xjzhu@cnic.cn"
  override val description: String = "Flink stream file sink."
  override val inportList: List[String] = List(Port.DefaultPort)
  override val outportList: List[String] = List(Port.DefaultPort)


  var path : String = _
  override def setProperties(map: Map[String, Any]): Unit = {

    path = MapUtil.get(map,"path").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val path = new PropertyDescriptor()
      .name("path")
      .displayName("Path")
      .description("save data into path.")
      .defaultValue("")
      .required(true)
      .example("/user/flink")

    descriptor = path :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/hive/SelectHiveQL.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.HiveGroup)
  }

  override def initialize(ctx: ProcessContext): Unit = {}

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val data = in.read().asInstanceOf[DataStream[String]]
    val sink: StreamingFileSink[String] = StreamingFileSink.forRowFormat(
      new Path(path),
      new SimpleStringEncoder[String]("UTF-8"))
      .build()
    data.addSink(sink)
  }
}
