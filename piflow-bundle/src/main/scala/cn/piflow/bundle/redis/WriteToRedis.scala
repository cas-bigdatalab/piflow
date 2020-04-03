package cn.piflow.bundle.redis


import cn.piflow.bundle.util.{JedisClusterImplSer, RedisUtil}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.sql.{DataFrame, SparkSession}
import redis.clients.jedis.HostAndPort


class WriteToRedis extends ConfigurableStop{
  override val authorEmail: String = "06whuxx@163.com"
  val description: String = "Write data to redis"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var redis_host:String =_
  var port:Int=_
  var password:String=_
  var column_name:String=_

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val df = in.read()
    var col_name:String=column_name
    df.printSchema()

    //connect to redis
    var jedisCluster=new JedisClusterImplSer(new HostAndPort(redis_host,port),password)

    df.collect.foreach(row=> {
      RedisUtil.manipulateRow(row,col_name,jedisCluster)
    })
    val v=jedisCluster.getJedisCluster.hkeys("aaa")
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

    val column_name = new PropertyDescriptor()
      .name("column_name")
      .displayName("Column_name")
      .description("The field in the schema you want to use as the key (must be unique)")
      .defaultValue("")
      .required(true)
      .example("id")
    descriptor = column_name :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/redis/WriteToRedis.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.RedisGroup)
  }

}
