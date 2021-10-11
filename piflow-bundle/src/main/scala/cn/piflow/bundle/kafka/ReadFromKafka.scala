package cn.piflow.bundle.kafka

import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.flink.streaming.api.scala.{DataStream, StreamExecutionEnvironment}
import org.apache.flink.types.Row


class ReadFromKafka extends ConfigurableStop{
  val description: String = "Read data from kafka"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)
  var kafka_host:String =_
  var topic:String=_
  var schema:String=_

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val flink = pec.get[StreamExecutionEnvironment]()
    val tableEnv = StreamTableEnvironment.create(flink)

    val kafkaSchema = new Schema()
    schema.split(",").map(x => x.trim).map(f => kafkaSchema.field(f,DataTypes.STRING()))

    tableEnv.connect(
      new Kafka()
        .version("0.11")
        .topic(topic)
        //        .startFromEarliest()
        //        .startFromLatest()
        .property("bootstrap.servers", kafka_host)
        .property("acks", "all")
        .property("group.id","mmmm")
        .property("enable.auto.commit","true")
        .property("max.poll.records","1000")
        .property("auto.offset.reset","earliest")
        .property("key.deserializer", "org.apache.kafka.common.serialization.StringDeserializer")
        .property("value.deserializer", "org.apache.kafka.common.serialization.StringDeserializer")
    ).withFormat(new Csv())
      .withSchema(kafkaSchema)
      .createTemporaryTable("kafkaInputTable")

    val kafkaTable:Table = tableEnv.from("kafkaInputTable")
    val appendStream:DataStream[Row] = tableEnv.toAppendStream[Row](kafkaTable)
    out.write(appendStream)
    //flink.execute("read from kafka")
  }
  def initialize(ctx: ProcessContext): Unit = {

  }


  def setProperties(map: Map[String, Any]): Unit = {
    kafka_host=MapUtil.get(map,key="kafka_host").asInstanceOf[String]
    topic=MapUtil.get(map,key="topic").asInstanceOf[String]
    schema=MapUtil.get(map,key="schema").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val kafka_host = new PropertyDescriptor().name("kafka_host").displayName("KAFKA_HOST").defaultValue("").required(true)
    val topic = new PropertyDescriptor().name("topic").displayName("TOPIC").defaultValue("").required(true)
    val schema = new PropertyDescriptor().name("schema").displayName("SCHEMA").defaultValue("").required(true)
    descriptor = kafka_host :: descriptor
    descriptor = topic :: descriptor
    descriptor = schema :: descriptor
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
