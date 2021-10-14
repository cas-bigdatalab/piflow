package cn.piflow.bundle.kafka

import java.util.Properties

import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.flink.api.common.serialization.SimpleStringSchema
import org.apache.flink.streaming.api.scala.{DataStream, StreamExecutionEnvironment}
import org.apache.flink.streaming.connectors.kafka.FlinkKafkaProducer
import org.apache.flink.streaming.connectors.kafka.internals.KeyedSerializationSchemaWrapper

class WriteToKafkaV2 extends ConfigurableStop{
  val description: String = "Write data to kafka"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)
  var kafka_host:String =_
  var topic:String=_

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    //val flink = pec.get[StreamExecutionEnvironment]()
    val data = in.read().asInstanceOf[DataStream[String]]

    val properties:Properties  = new Properties()
    properties.put("bootstrap.servers", kafka_host)
    properties.put("acks", "all")
    //properties.put("retries", 0)
    //properties.put("batch.size", 16384)
    //properties.put("linger.ms", 1)
    //properties.put("buffer.memory", 33554432)
    //properties.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer")
    //properties.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer")

    data.addSink(new FlinkKafkaProducer[String](
      topic,
      new KeyedSerializationSchemaWrapper[String](new SimpleStringSchema()),
      properties,
      FlinkKafkaProducer.Semantic.EXACTLY_ONCE))

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
