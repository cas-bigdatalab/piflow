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

  override val authorEmail: String = "06whuxx@163.com"
  val description: String = "Read data from redis"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

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

    val fields:Array[String]=schema.split(",").map(x => x.trim)
    val col_str:String=column_name+","+schema
    val newSchema:Array[String]=col_str.split(",").map(x => x.trim)

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
    val df=spark.createDataFrame(newRDD,dfSchema)
    out.write(df)
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

    val redis_host = new PropertyDescriptor()
      .name("redis_host")
      .displayName("Redis_Host")
      .description("The host of Redis")
      .defaultValue("")
      .required(true)
      .example("127.0.0.1")
    descriptor = redis_host :: descriptor

    val port = new PropertyDescriptor()
      .name("port")
      .displayName("Port")
      .description("Port to connect to Redis")
      .defaultValue("")
      .required(true)
      .example("7000")
    descriptor = port :: descriptor

    val password = new PropertyDescriptor()
      .name("password")
      .displayName("Password")
      .description("The password of Redis")
      .defaultValue("")
      .required(true)
      .example("123456")
      .sensitive(true)
    descriptor = password :: descriptor

    val schema = new PropertyDescriptor()
      .name("schema")
      .displayName("Schema")
      .description("The field you want to fetch from redis based on the key")
      .defaultValue("")
      .required(true)
      .example("id,name")
    descriptor = schema :: descriptor

    val column_name = new PropertyDescriptor()
      .name("column_name")
      .displayName("Column_Name")
      .description("This column is your key to fetch data from redis")
      .defaultValue("")
      .required(true)
      .example("gender")
    descriptor = column_name :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/redis/ReadFromRedis.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.RedisGroup)
  }

}
