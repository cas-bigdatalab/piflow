package cn.piflow.bundle.redis


import cn.piflow.bundle.util.{JedisClusterImplSer, RedisUtil}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.MapUtil
import org.apache.spark.sql.{DataFrame, SparkSession}
import redis.clients.jedis.HostAndPort


class WriteToRedis extends ConfigurableStop{
  val description: String = "Write data to redis."
  val inportCount: Int = 1
  val outportCount: Int = 0
  var redis_host:String =_
  var port:Int=_
  var password:String=_
  var column_name:String=_
  //var schema_str:String=_

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val df = in.read()
    var col_name:String=column_name

    println(df.schema)
    //connect to redis
    var jedisCluster=new JedisClusterImplSer(new HostAndPort(redis_host,port),password)
    df.collect.foreach(row=> {
      RedisUtil.manipulateRow(row,col_name,jedisCluster)
    })
    //val v=jedisCluster.getJedisCluster.hmget("Python","author","pages")
    val v=jedisCluster.getJedisCluster.hkeys("Python")
    println(v)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }


  def setProperties(map: Map[String, Any]): Unit = {
    redis_host=MapUtil.get(map,key="redis_host").asInstanceOf[String]
    port=Integer.parseInt(MapUtil.get(map,key="port").toString)
    password=MapUtil.get(map,key="password").asInstanceOf[String]
    column_name=MapUtil.get(map,key="column_name").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val redis_host = new PropertyDescriptor().name("redis_host").displayName("REDIS_HOST").defaultValue("").required(true)
    val port = new PropertyDescriptor().name("port").displayName("PORT").defaultValue("").required(true)
    val password = new PropertyDescriptor().name("password").displayName("PASSWORD").defaultValue("").required(true)
    val column_name = new PropertyDescriptor().name("column_name").displayName("COLUMN_NAME").defaultValue("").required(true)
    descriptor = redis_host :: descriptor
    descriptor = port :: descriptor
    descriptor = password :: descriptor
    descriptor = column_name :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = ???

  override def getGroup(): List[String] = {
    List(StopGroupEnum.RedisGroup.toString)
  }

  override val authorEmail: String = "xiaoxiao@cnic.cn"
}
