package cn.piflow.bundle.nsfc.distinct

import cn.piflow.bundle.util.JedisClusterImplSer
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import redis.clients.jedis.HostAndPort

class RedisDistinctCachePersist extends ConfigurableStop {
  override val authorEmail: String = "xiaomeng7890@gmail.com"
  override val description: String = "persist the df into redis server, which will be used to distinct"
  override val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  override val outportList: List[String] = List(PortEnum.DefaultPort.toString)

  var persist_needed_fields : String = _
  var persist_primary_field : String = _
  var distinct_rule : String = _
  var redis_server_ip : String = _
  var redis_server_port : Int = _
  var redis_server_passwd : String = _
  var jedisCluster : JedisClusterImplSer = _
  override def setProperties(map: Map[String, Any]): Unit = {
    persist_needed_fields = MapUtil.get(map,"distinct field").asInstanceOf[String]
    persist_primary_field = MapUtil.get(map,"primary field").asInstanceOf[String]
    distinct_rule = MapUtil.get(map,"distinct rule").asInstanceOf[String]
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

    val primary_field = new PropertyDescriptor().
      name("primary field").
      displayName("primary field").
      description("the primary key").
      defaultValue("psn_code").
      required(true)
    descriptor = primary_field :: descriptor

    val distinct_field = new PropertyDescriptor().
      name("distinct field").
      displayName("distinct field").
      description("the fields needed in distinct and distinct rule").
      defaultValue("zh_name,email,tel").
      required(true)
    descriptor = distinct_field :: descriptor

    val distinct_rule = new PropertyDescriptor().
      name("distinct rule").
      displayName("distinct rule").
      description("the rule to organize distinct").
      defaultValue("zh_name&email,zh_name&tel").
      required(true)
    descriptor = distinct_rule :: descriptor


    descriptor
  }

  override def getIcon(): Array[Byte] = ImageUtil.getImage("icon/hive/SelectHiveQL.png")

  override def getGroup(): List[String] =  List(StopGroup.NSFC.toString, "sha0w", "distinct")

  override def initialize(ctx: ProcessContext): Unit = {
    jedisCluster = new JedisClusterImplSer(new HostAndPort(redis_server_ip, redis_server_port), redis_server_passwd)
  }
  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val df = in.read()
    val mPrimaryKeyIndex = df.schema.fieldIndex(persist_primary_field) //PSNCODE
    val df_mperson_fields = persist_needed_fields.split(",").+:(persist_primary_field)
    val s1 = df_mperson_fields.map(i => (i, {
      df.schema.fieldIndex(i)
    })).toMap[String, Int] //生产字段名 -》 index的键值对
    df.rdd.foreach(
      row => {
        cn.piflow.bundle.util.RedisUtil.putRedis(
          row, s1, distinct_rule, mPrimaryKeyIndex, jedisCluster.getJedisCluster) // create the redis dataset
      }
    )
    jedisCluster.close()
    out.write(df)
  }
}
