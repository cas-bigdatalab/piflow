package cn.piflow.bundle.redis


import java.util

import cn.piflow.bundle.util.{JedisClusterImplSer, RedisUtil}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.avro.generic.GenericData.StringType
import org.apache.spark.sql.catalyst.encoders.RowEncoder
import org.apache.spark.sql.types.{DataType, StructField, StructType}
import org.apache.spark.sql.{DataFrame, Row, SparkSession}
import redis.clients.jedis.{HostAndPort, Jedis, JedisCluster}

import scala.collection.mutable.ArrayBuffer


class ReadFromRedis extends ConfigurableStop{
  val description: String = "Read data from redis."
  val inportList: List[String] = List(PortEnum.NonePort.toString)
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)
  var redis_host:String =_
  var port:Int=_
  var password:String=_
  var column_name:String=_
  var schema:String=_

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()

    var dfIn=in.read()
    var colName=column_name

    //connect to redis
    val jedisCluster=new JedisClusterImplSer(new HostAndPort(redis_host,port),password)

    //val keysArray:Array[String]=keys.split(",")
    val fields:Array[String]=schema.split(",")
    val col_str:String=column_name+","+schema
    val newSchema:Array[String]=col_str.split(",")
    //var res:List[List[String]]=List()

    //import org.apache.spark.sql.types._
    val dfSchema=StructType(newSchema.map(f=>StructField(f,org.apache.spark.sql.types.StringType,true)))


    val newRDD=dfIn.rdd.map(line=>{
      import spark.implicits._
      val row=new ArrayBuffer[String]
      val key=line.getAs[String](colName)
      row += key
      for(j<-0 until fields.length){
        row += jedisCluster.getJedisCluster.hget(key,fields(j))
      }
      Row.fromSeq(row.toArray.toSeq)
    })
    //val df=spark.createDataFrame(newRDD,dfSchema)
    //newRDD.show(20)
    //out.write(df)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }


  def setProperties(map: Map[String, Any]): Unit = {
    redis_host=MapUtil.get(map,key="redis_host").asInstanceOf[String]
    port=Integer.parseInt(MapUtil.get(map,key="port").toString)
    password=MapUtil.get(map,key="password").asInstanceOf[String]
    schema=MapUtil.get(map,key="schema").asInstanceOf[String]
    column_name=MapUtil.get(map,key="column_name").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val redis_host = new PropertyDescriptor().name("redis_host").displayName("REDIS_HOST").defaultValue("").required(true)
    val port = new PropertyDescriptor().name("port").displayName("PORT").defaultValue("").required(true)
    val password = new PropertyDescriptor().name("password").displayName("PASSWORD").defaultValue("").required(true)
    val schema = new PropertyDescriptor().name("schema").displayName("SCHEMA").defaultValue("").required(true)
    val column_name = new PropertyDescriptor().name("column_name").displayName("COLUMN_NAME").defaultValue("").required(true)
    descriptor = redis_host :: descriptor
    descriptor = port :: descriptor
    descriptor = password :: descriptor
    descriptor = schema :: descriptor
    descriptor = column_name :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("redis.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroupEnum.RedisGroup.toString)
  }

  override val authorEmail: String = "xiaoxiao@cnic.cn"
}
