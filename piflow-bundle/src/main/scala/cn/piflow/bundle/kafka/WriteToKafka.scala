package cn.piflow.bundle.kafka

import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.flink.streaming.api.scala.{DataStream, StreamExecutionEnvironment}
import org.apache.flink.table.api.Table
import org.apache.flink.table.api.bridge.scala.StreamTableEnvironment
import org.apache.flink.table.descriptors.{Csv, Kafka, Schema}
import org.apache.flink.types.Row

class WriteToKafka extends ConfigurableStop{
  val description: String = "Write data to kafka"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)
  var kafka_host:String =_
  var topic:String=_

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val flink = pec.get[StreamExecutionEnvironment]()
    val tableEnv = StreamTableEnvironment.create(flink)
    val inputStream = in.read().asInstanceOf[DataStream[Row]]
    val kafkaTable: Table = tableEnv.fromDataStream(inputStream)
    val fieldNames = kafkaTable.getSchema.getFieldNames
    var fields = ""
    for(i <- 0 until fieldNames.size){
      if(i == fieldNames.size-1 ) fields +="`" + fieldNames(i) + "`" + " STRING"
      else fields +="`" + fieldNames(i) + "`" + " STRING,"
    }

    tableEnv.executeSql(
      "create table kafkaOutputTable(" +
        fields +
        ")with(" +
        "'connector' = 'kafka'," +
        "'topic' = '"+topic+"'," +
        "'properties.bootstrap.servers' = '"+kafka_host+"'," +
        "'properties.group.id' = 'mmmm',"+
        "'properties.acks' = 'all'," +
        "'scan.startup.mode' = 'earliest-offset'," +
        "'format' = 'csv'," +
        "'csv.field-delimiter' = ','" +
        ")")

    kafkaTable.executeInsert("kafkaOutputTable");
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
