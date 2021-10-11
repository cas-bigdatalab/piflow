package cn.piflow.bundle.kafka

import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.flink.api.common.serialization.SimpleStringSchema
import org.apache.flink.streaming.api.scala.{DataStream, StreamExecutionEnvironment}
import org.apache.flink.streaming.connectors.kafka.FlinkKafkaProducer011

class WriteToKafkaV2 extends ConfigurableStop{
  val description: String = "Write data to kafka"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)
  var kafka_host:String =_
  var topic:String=_

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    //val flink = pec.get[StreamExecutionEnvironment]()
    val data = in.read().asInstanceOf[DataStream[String]]
    data.addSink(new FlinkKafkaProducer011[String](kafka_host, topic, new SimpleStringSchema()))
    //flink.execute()
  }


  def initialize(ctx: ProcessContext): Unit = {

  }


  def setProperties(map: Map[String, Any]): Unit = {
    kafka_host=MapUtil.get(map,key="kafka_host").asInstanceOf[String]
    //port=Integer.parseInt(MapUtil.get(map,key="port").toString)
    topic=MapUtil.get(map,key="topic").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val kafka_host = new PropertyDescriptor().name("kafka_host").displayName("KAFKA_HOST").defaultValue("").required(true)
    val topic = new PropertyDescriptor().name("topic").displayName("TOPIC").defaultValue("").required(true)
    descriptor = kafka_host :: descriptor
    descriptor = topic :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/kafka/WriteToKafka.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.KafkaGroup.toString)
  }

  override val authorEmail: String = "liangdchg@163.com"
}
