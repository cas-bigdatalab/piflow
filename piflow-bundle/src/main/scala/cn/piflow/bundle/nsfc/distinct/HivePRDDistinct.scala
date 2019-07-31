package cn.piflow.bundle.nsfc.distinct

import java.util.UUID

import cn.piflow.bundle.util.JedisClusterImplSer
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.types.StructType
import org.apache.spark.sql.{Column, Row, SparkSession}
import redis.clients.jedis.{HostAndPort, JedisCluster}

class HivePRDDistinct extends ConfigurableStop {
  override val authorEmail: String = "xiaomeng7890@gmail.com"
  override val description: String = ""
  //
  override val inportList: List[String] = List("productTable","productSpecTable")
  override val outportList: List[String] = List("Relation", "Entity")

  var processUseKey : String = "product_id,zh_title,authors,en_title"
  var rule : String = "zh_title&authors,en_title&authors,product_id"
  lazy val recordKey = "id"
  lazy val psn = "psn_code"
  lazy val pro = "product_id"


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

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val df = in.read()
    val ss = pec.get[SparkSession]()
    val relation_df = df.select(Seq[String](recordKey, psn, pro).map(s => new Column(s)) : _*)
    val cols = df.columns
    var union_schema = df.schema
    //get used key
    val useKey = cols.array

    val processUseKeyArray = processUseKey.split(",")
    val useCol = useKey.
      filter(s => {processUseKeyArray.contains(s)}).
      map(x => new Column(x))
    var require_df = df.select(useCol : _*)

    var require_schema = require_df.schema
    var recordIndex = require_schema.fieldIndex(pro)
    //check point
    var require_rdd = require_df.rdd
    println("================================================")

    println("================================================")
    //dup
    val processKeyArray = rule.split(",")
    processKeyArray.foreach(key => {
      require_rdd = require_rdd.map(row => (this.mkRowKey(require_schema, row, key).trim, row))
        .groupByKey()
        .map(i => (i._1 , {
          recordMKDup(i._2, recordIndex, jedisCluster.getJedisCluster)//记录
        })) //opt:R/W deliver this part record the mk Dup
        .values
        .filter(r => {
          r != null
        }) //reduce can combine two duplicate value)
    })
    println( "temp size is : ====> + : " + require_rdd.count())
    //dup up
    val back_to_hive_rdd = df.rdd.map(row => {
      (this.getMKFather(row.getString(union_schema.fieldIndex(pro)), jedisCluster.getJedisCluster),row)
    }) .groupByKey()
      .map(i => {
        val rows = i._2.toArray
        gatherDup(rows, union_schema.fieldIndex(recordKey), i._1)
      })
    println( "back to hive size is : ====> + : " + back_to_hive_rdd.count())
    val hive_df = ss.createDataFrame(back_to_hive_rdd, union_schema)
    val relaSchema = relation_df.schema
    val product_index_rela = relaSchema.fieldIndex(pro)

    val relation_rdd_afwash = relation_df.rdd.map(r => {
      val pro_id = r.getString(product_index_rela)
      Row.fromSeq(r.toSeq.updated(product_index_rela, getMKFather(pro_id, jedisCluster.getJedisCluster)))
    })
    val relation_df_afwash = ss.createDataFrame(relation_rdd_afwash, relaSchema)
    out.write("Entity", hive_df)
    out.write("Relation", relation_df_afwash)
  }
  def getMKFather(key:String,jedisCluster: JedisCluster): String = {
    val s = jedisCluster.hget("product_table_dup@" + key, "product:MK - S")
    if (s == null || s == key) key //not son of any return itself
    // I know you will feel confuse , just relax :-)
    else getMKFather(s,jedisCluster)
  }
  def gatherDup(rows : Array[Row], primaryKeyIndex:Int, primaryKey : String): Row = {
    var f = rows.head //rows length >= 1
    if (rows.length < 2) return f //only one elem
    var father = f.toSeq.toArray
    for (index <- 1 until rows.length) {
      var row = rows(index)
      if (row != null && f != null){ //null pointer
        father = gatherDup_(father, row.toSeq.toArray, primaryKeyIndex, primaryKey)
      }
    }
    Row.fromSeq(father.toSeq)
  }
  def gatherDup_(a: Array[Any], b: Array[Any], Pindex:Int, PK: String): Array[Any] = {
    for (indi <- a.indices) {
      if (a(indi) == null)
        a.update(indi, b(indi))
    }
    a.update(Pindex, PK) //set father key to this
    a
  }
  def buildNewRow (before : Seq[Any], beforeSchema:StructType, afterSchema:StructType): Row = {
    var afterSeq = scala.collection.mutable.ArraySeq[Any]()
    for (index <- 0 until afterSchema.length) {
      afterSeq = afterSeq.:+(before(beforeSchema.fieldIndex(afterSchema(index).name)))
    }
    Row.fromSeq(afterSeq)
  }
  def resetRedis(jedisCluster: JedisCluster): Unit = {
    import scala.collection.JavaConversions._
    for (pool <- jedisCluster.getClusterNodes.values) {
      try {
        val jedis = pool.getResource
        try
          jedis.flushAll
        catch {
          case ex: Exception =>
            System.out.println(ex.getMessage)
        } finally if (jedis != null) jedis.close()
      }
    }
  }

  def getPositive(i : Int): String = {
    if (i < 0) "n" + (i * -1).toString
    else i.toString
  }

  def recordMKDup(row1: Row, row2:Row , primaryKeyIndex:Int, jedisCluster: JedisCluster) : Row = {
    if (row2 == null) return row1 //only one elem
    jedisCluster.hset("product_table_dup@" + row2.getString(primaryKeyIndex), "product:MK - S", row1.getString(primaryKeyIndex)) //set son =:MK - S=> father (1 -> 1)
    row1
  }
  def recordMKDup(rows: Iterable[Row],primaryKeyIndex:Int, jedisCluster: JedisCluster) :Row = {
    var f = rows.head //rows length >= 1
    if (rows.size < 2) return f //only one elem
    for (row <- rows) {
      jedisCluster.hset("product_table_dup@" + row.getString(primaryKeyIndex), "product:MK - S", f.getString(primaryKeyIndex)) //set son =:MK - S=> father (1 -> 1)
    }
    f
  }
  def keys(pattern: String, jedisCluster: JedisCluster): Set[String] = {
    var keys = Set[String]()
    val clusterNodes = jedisCluster.getClusterNodes
    import scala.collection.JavaConversions._
    for (k <- clusterNodes.keySet) {
      val jp = clusterNodes.get(k)
      try {
        val connection = jp.getResource
        try
          keys = keys.++:(connection.keys(pattern))
        catch {
          case ignored: Exception =>
        } finally if (connection != null) connection.close()
      }
    }
    keys
  }
  def mkRowKey(schema_result:StructType, row: Row, key : String): String = {
    var hasNull = false
    var s = ""
    if (key.contains("&")) {
      val sl = key.split("&")
      sl.foreach(s_ => {
        val index = schema_result.fieldIndex(s_)
        if (row.isNullAt(index) || (row.getAs[String](index) == "null")) {
          hasNull = true
        } else {
          s += row.getAs[String](index)
        }
      })
    } else {
      val index = schema_result.fieldIndex(key)
      if (row.isNullAt(index) || (row.getString(index) == "null")) {
        hasNull = true
      } else {
        s = row.getAs[String](index)
      }
    }
    if (hasNull) {
      s = UUID.randomUUID().toString
    }
    s
  }
}
