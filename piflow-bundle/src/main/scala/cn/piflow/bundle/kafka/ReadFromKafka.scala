package cn.piflow.bundle.kafka

import java.util
import java.util.{Collections, Properties}

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.bundle.util.JedisClusterImplSer
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.MapUtil
import org.apache.spark.sql.{Row, SparkSession}
import org.apache.spark.sql.types.{StructField, StructType}

import scala.collection.mutable.ArrayBuffer
import org.apache.kafka.clients.consumer.ConsumerRecord
import org.apache.kafka.clients.consumer.ConsumerRecords
import org.apache.kafka.clients.consumer.KafkaConsumer
import org.apache.kafka.common.serialization.StringSerializer


class ReadFromKafka extends ConfigurableStop{
  val inportCount: Int = 1
  val outportCount: Int = 0
  var kafka_host:String =_
  var topic:String=_
  var schema:String=_

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()

    val properties:Properties  = new Properties()
    import org.apache.kafka.clients.producer.ProducerConfig
    properties.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, kafka_host)
    properties.put("acks", "all")
    properties.put("group.id","b")
    properties.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, classOf[StringSerializer].getName)
    properties.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, classOf[StringSerializer].getName)
    properties.put("key.deserializer", "org.apache.kafka.common.serialization.StringDeserializer")
    properties.put("value.deserializer", "org.apache.kafka.common.serialization.StringDeserializer")

    //properties.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer")
    //properties.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer")



    //val fields:Array[String]=schema.split(",")
    //val newSchema:Array[String]=col_str.split(",")

    var res:List[Array[String]]=List()

    //import org.apache.spark.sql.types._
    //val dfSchema=StructType(newSchema.map(f=>StructField(f,org.apache.spark.sql.types.StringType,true)))

    val consumer = new KafkaConsumer[String,String](properties)
    consumer.subscribe(Collections.singleton(topic))
    val records:ConsumerRecords[String,String] = consumer.poll(100)
    val it=records.iterator()
    while(it.hasNext){
        //println(it.next().value())
        val row=it.next().value().split(",")
        res = row::res
    }
    import spark.implicits._
    val schemaArr = schema.split(",")
    val newDF=spark.sparkContext.parallelize(res).toDF(schemaArr:_*)
    //newRDD.show(20)
    //out.write(df)
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

  override def getIcon(): Array[Byte] = ???

  override def getGroup(): List[String] = {
    List(StopGroupEnum.KafkaGroup.toString)
  }

  override val authorEmail: String = "xiaoxiao@cnic.cn"
}
