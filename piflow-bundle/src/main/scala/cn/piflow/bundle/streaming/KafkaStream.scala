package cn.piflow.bundle.streaming

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStreamingStop, PortEnum, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.kafka.common.serialization.StringDeserializer
import org.apache.spark.streaming.StreamingContext
import org.apache.spark.streaming.dstream.DStream
import org.apache.spark.streaming.kafka010.KafkaUtils
import org.apache.spark.streaming.kafka010.LocationStrategies.PreferConsistent
import org.apache.spark.streaming.kafka010.ConsumerStrategies.Subscribe


class KafkaStream extends ConfigurableStreamingStop{
  override val timing: Integer = 1
  override val authorEmail: String = "xjzhu@cnic.cn"
  override val description: String = "read data from kafka."
  override val inportList: List[String] = List(PortEnum.NonePort)
  override val outportList: List[String] = List(PortEnum.DefaultPort)

  var brokers:String = _
  var groupId:String = _
  var topics:Array[String] = _
  override def setProperties(map: Map[String, Any]): Unit = {
    brokers=MapUtil.get(map,key="brokers").asInstanceOf[String]
    groupId=MapUtil.get(map,key="groupId").asInstanceOf[String]
    topics=MapUtil.get(map,key="topics").asInstanceOf[String].split(",")
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val brokers = new PropertyDescriptor().name("brokers").displayName("brokers").description("kafka brokers, seperated by ','").defaultValue("").required(true)
    val groupId = new PropertyDescriptor().name("groupId").displayName("groupId").description("kafka consumer group").defaultValue("group").required(true)
    val topics = new PropertyDescriptor().name("topics").displayName("topics").description("kafka topics").defaultValue("").required(true)
    descriptor = brokers :: descriptor
    descriptor = groupId :: descriptor
    descriptor = topics :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("mllib.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.StreamingGroup)
  }

  override def getDStream(ssc: StreamingContext): DStream[String] = {
    val kafkaParams = Map[String, Object](
      "bootstrap.servers" -> brokers,
      "key.deserializer" -> classOf[StringDeserializer],
      "value.deserializer" -> classOf[StringDeserializer],
      "group.id" -> groupId,
      "auto.offset.reset" -> "latest",
      "enable.auto.commit" -> (false:java.lang.Boolean)
    )
    val stream = KafkaUtils.createDirectStream[String,String](
      ssc,
      PreferConsistent,
      Subscribe[String, String](topics, kafkaParams)
    )
    stream.map(record => record.key() + "," + record.value())
    //stream.asInstanceOf[DStream[ConsumerRecord]]

  }

  override def initialize(ctx: ProcessContext): Unit = {}

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {}
}
