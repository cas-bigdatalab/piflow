package cn.piflow.bundle.nsfc.distinct

import cn.piflow.bundle.util.JedisClusterImplSer
import cn.piflow.conf.{ConfigurableStop, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.SparkContext
import org.apache.spark.sql.{DataFrame, Row, SQLContext}
import redis.clients.jedis.HostAndPort

/**
  * HIVE JDBC DRIVER DESIGN FOR HIVE 1.2.1
  */
class HivePRDDistinct extends ConfigurableStop {
  override val authorEmail: String = "xiaomeng7890@gmail.com"
  override val description: String = ""
  //
  override val inportList: List[String] = List("productTable","productSpecTable")
  override val outportList: List[String] = List("Relation", "Entity")

  var processuserKey : String = _
  var psnPrimary : String = _
  var productPrimary : String = _

  var redis_server_ip : String = _
  var redis_server_port : Int = _
  var redis_server_passwd : String = _
  var jedisCluster : JedisClusterImplSer = _


  override def setProperties(map: Map[String, Any]): Unit = {
    redis_server_ip = MapUtil.get(map,"redis ip").asInstanceOf[String]
    redis_server_port = MapUtil.get(map,"redis port").asInstanceOf[Int]
    redis_server_passwd = MapUtil.get(map,"redis passwd").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val redis_passwd = new PropertyDescriptor().
      name("redis passwd").
      displayName("redis passwd").
      description("redis server passwd").
      required(true)
    descriptor = redis_passwd :: descriptor

    val redis_port = new PropertyDescriptor().
      name("redis port").
      displayName("redis port").
      description("redis server port").
      required(true)
    descriptor = redis_port :: descriptor

    val redis_server = new PropertyDescriptor().
      name("redis server").
      displayName("redis server").
      description("redis server ip").
      required(true)
    descriptor = redis_server :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] =   ImageUtil.getImage("icon/hive/SelectHiveQL.png")

  override def getGroup(): List[String] = {
    List(StopGroup.NSFC.toString, "sha0w", "distinct", "product")
  }

  override def initialize(ctx: ProcessContext): Unit = {
    jedisCluster = new JedisClusterImplSer(new HostAndPort(redis_server_ip, redis_server_port), redis_server_passwd)
  }

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = ???



}