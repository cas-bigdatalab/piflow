package cn.piflow.bundle.kafka

import java.util.Properties

import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.flink.api.common.serialization.SimpleStringSchema
import org.apache.flink.streaming.api.scala.{DataStream, StreamExecutionEnvironment}
import org.apache.kafka.common.serialization.StringSerializer


class ReadFromKafkaV2 extends ConfigurableStop{
  val description: String = "Read data from kafka"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)
  var kafka_host:String =_
  var topic:String=_

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val flink = pec.get[StreamExecutionEnvironment]()

    val properties:Properties  = new Properties()
    import org.apache.kafka.clients.producer.ProducerConfig
    properties.put("bootstrap.servers", kafka_host)
    properties.put("acks", "all")
    properties.put("group.id","mmmm")
    properties.put("enable.auto.commit","true")
    properties.put("max.poll.records","1000")
    properties.put("auto.offset.reset","earliest")
    properties.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, classOf[StringSerializer].getName)
    properties.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, classOf[StringSerializer].getName)
    properties.put("key.deserializer", "org.apache.kafka.common.serialization.StringDeserializer")
    properties.put("value.deserializer", "org.apache.kafka.common.serialization.StringDeserializer")

    //properties.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer")
    //properties.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer")

    val kafkaDS: DataStream[String] = flink.addSource( new FlinkKafkaConsumer011[String](topic,new SimpleStringSchema(),properties))
    out.write(kafkaDS)
    //flink.execute()
  }
  def initialize(ctx: ProcessContext): Unit = {

  }


  def setProperties(map: Map[String, Any]): Unit = {
    kafka_host=MapUtil.get(map,key="kafka_host").asInstanceOf[String]
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
    ImageUtil.getImage("icon/kafka/ReadFromKafka.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.KafkaGroup.toString)
  }

  override val authorEmail: String = "liangdchg@163.com"
}
