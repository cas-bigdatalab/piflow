package cn.piflow.bundle.nsfc.distinct

import cn.piflow.bundle.util.JedisClusterImplSer
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.sql.{Row, SparkSession}
import redis.clients.jedis.{HostAndPort, JedisCluster}

class foreignKeyWash extends ConfigurableStop {
  override val authorEmail: String = "xiaomeng7890@gmail.com"
  override val description: String = ""
  //
  var washField : String = _
  var redis_server_ip : String = _
  var redis_server_port : Int = _
  var redis_server_passwd : String = _
  var jedisCluster : JedisClusterImplSer = _

  override val inportList: List[String] = List(Port.DefaultPort.toString)
  override val outportList: List[String] = List(Port.DefaultPort.toString)

  override def setProperties(map: Map[String, Any]): Unit = {
    redis_server_ip = MapUtil.get(map,"redis ip").asInstanceOf[String]
    redis_server_port = MapUtil.get(map,"redis port").asInstanceOf[Int]
    redis_server_passwd = MapUtil.get(map,"redis passwd").asInstanceOf[String]
    washField = MapUtil.get(map,"wash field").asInstanceOf[String]
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

    val wash_field = new PropertyDescriptor().
      name("wash field").
      displayName("wash field").
      description("the foreign key you need wash").
      required(true)
    descriptor = wash_field :: descriptor

    descriptor
  }
  override def getIcon(): Array[Byte] =   ImageUtil.getImage("icon/hive/SelectHiveQL.png")

  override def getGroup(): List[String] = {
    List(StopGroup.NSFC.toString, "sha0w", "distinct", "foreignKey")
  }


  override def initialize(ctx: ProcessContext): Unit = {
    jedisCluster = new JedisClusterImplSer(new HostAndPort(redis_server_ip, redis_server_port), redis_server_passwd)
  }

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val washTable = in.read()
    val ss = pec.get[SparkSession]()
    val acc = ss.sparkContext.accumulator[Int](0,"changeCount")
    val washTableSchema = washTable.schema
    val washIndex = washTableSchema.fieldIndex(washField)
    val washTableRdd = washTable.rdd
    val afterWash = washTableRdd
      .map(row => row.toSeq)
      .map(seq => {
        val key = getMKFather(seq(washIndex).asInstanceOf[String], jedisCluster.getJedisCluster)
        if (key != seq(washIndex)) {
          seq.updated(washIndex, key)
          acc += 1
        }
        seq
      }
      ).map(r => Row.fromSeq(r))

    val bkDF = ss.createDataFrame(afterWash, washTableSchema)
    println(bkDF.count())
    println("====================================")
    println(acc.name.get+" : "+acc.value)
    out.write(bkDF)
  }

  def getMKFather(key:String, jedisCluster: JedisCluster): String = {
    val s = jedisCluster.hget("product_table_dup@" + key, "product:MK - S")
    if (s == null || s == key) key //not son of any return itself
    // I know you will feel confuse , just relax :-)
    else getMKFather(s, jedisCluster)
  }
}
