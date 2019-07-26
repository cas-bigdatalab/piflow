package cn.piflow.bundle.nsfc.distinct

import cn.piflow.bundle.util.JedisClusterImplSer
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.rdd.RDD
import org.apache.spark.sql.types.{StringType, StructField, StructType}
import org.apache.spark.sql.{Column, DataFrame, Row, SaveMode, SparkSession, TypedColumn}
import redis.clients.jedis.HostAndPort

class HivePSNDistinct extends ConfigurableStop{
  override val authorEmail: String = "xiaomeng7890@gmail.com"
  override val description: String = ""
  override val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  override val outportList: List[String] = List("Relation", "Entity")

  var tableName : String = _ //after wash
  var sourceField : String = _
  var timeField : String = _
  var idKey : String = _
  var noChange : Boolean = _
  var distinctRule : String = _
  var distinctFields : String = _
  var primaryKey : String = _
  var distinctTableType : String = _
  var rel_fields : String = _ //"id,prj_code,psn_code"
  var used_fields : String = _ //"id,psn_code,zh_name,id_type,id_no,birthday,gender,degree_code,nation,tel,email,org_code,zero,identity_card,military_id,passport,four,home_return_permit,mainland_travel_permit_for_taiwan_residents"


  var redis_server_ip : String = _
  var redis_server_port : Int = _
  var redis_server_passwd : String = _

  var jedisCluster : JedisClusterImplSer = _
  //  val subTableName = _
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
    List(StopGroup.NSFC.toString, "sha0w", "distinct")
  }

  override def initialize(ctx: ProcessContext): Unit = {
    jedisCluster = new JedisClusterImplSer(new HostAndPort(redis_server_ip, redis_server_port), redis_server_passwd)
  }

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    if (noChange){
      out.write(in.read())
      return
    }
    val inDF = in.read().select(used_fields.split(",").map(s => new Column(s)) : _*)

    val spark = pec.get[SparkSession]()
    val inSchema = inDF.schema
    val primaryIndex = inDF.schema.fieldIndex(primaryKey)
    var pairRDD = inDF.rdd.map(row => (row.getString(primaryIndex), {
      row
    }))
    var processKeyArray = distinctFields.split(",")
    processKeyArray +:= idKey
    processKeyArray.foreach(key => { //对这里的每一组key
      pairRDD = pairRDD.map(row => (cn.piflow.bundle.util.NSFCUtil.mkRowKey(inSchema, row._2, key), row)) //生成key pair， 若key不存在则生成UUID
        .groupByKey
        .map(i => (i._1 , {
          cn.piflow.bundle.util.RedisUtil.recordMKDup(i._2, tableName ,jedisCluster.getJedisCluster) //Mark需要合并的key
        })) //opt:R/W deliver this part record the mk Dup
        .values
        .filter(r => {
          r._2 != null
        }) //reduce can combine two duplicate value)
    })
    var keykeyRDD = pairRDD.map(r => (r._1, cn.piflow.bundle.util.RedisUtil.checkRedis(r, inSchema, tableName,distinctTableType, distinctRule.split(",") , jedisCluster.getJedisCluster),r._2))

    var backToHiveRdd = keykeyRDD.map(r => (r._1, {
      var row = r._3
      var psn = r._2
      var id = r._1
      var rowArray = row.toSeq
      jedisCluster.getJedisCluster.hset(tableName + "@" + id, distinctTableType + "IdPSN" , psn)
      Row.fromSeq(rowArray.updated(primaryIndex,psn))
    })).filter(r => {
      !jedisCluster.getJedisCluster.hexists(tableName + "@" + r._1, distinctTableType + "PSNExist")
    }).values
    println("=====================" + backToHiveRdd.count + "========================") //active
    val df_backToHive = spark.sqlContext.createDataFrame(
      backToHiveRdd, inSchema
    )
    val rel_fields_arr = rel_fields.split(",")
    if (rel_fields_arr.size == 3) {
      var df_relationship : DataFrame = inDF.select(rel_fields_arr.map(x => new Column(x)) : _*)
      //此处应对pj_member进行映射
      var rela_schema = df_relationship.schema
      var relation_rdd = df_relationship.rdd
      val id_1 = rel_fields_arr(0) //id
      val id_2 = rel_fields_arr(1) //prj
      val id_3 = rel_fields_arr(2) //psn

      var backToHiveRelation = relation_rdd.map(row => (row.getString(rela_schema.fieldIndex(id_1))
        ,row.getString(rela_schema.fieldIndex(id_2))))
        .map(r => (r._1, r._2, cn.piflow.bundle.util.RedisUtil.getMKFather(r._1, tableName, distinctTableType,  jedisCluster.getJedisCluster)
        )).map(i => Row.fromSeq(Array(i._1,i._2,i._3)))
      var df_backToHiveRelation = spark.sqlContext.createDataFrame(backToHiveRelation, rela_schema)
      jedisCluster.close()
      out.write("Relation", df_backToHiveRelation)
    }
    else {
      var df_relationship : DataFrame = inDF.select(rel_fields_arr.map(x => new Column(x)) : _*)
      if (rel_fields_arr.size != 4) throw new Exception("wrong input rel schema size, should be 3 or 4")
      var rela_schema = StructType(rel_fields_arr.map(StructField(_, StringType, nullable = true)))
      var relation_rdd = df_relationship.rdd.map(i => {Row.fromSeq(i.toSeq.+:(cn.piflow.bundle.util.NSFCUtil.generateUUID()))})
      //id,prp_code,psn_code,seq_no
      var backToHiveRelation =
        relation_rdd.
          map(row => (row.getString(rela_schema.fieldIndex(rel_fields_arr(0))),
            row.getString(rela_schema.fieldIndex(rel_fields_arr(1))),
            row.getString(rela_schema.fieldIndex(rel_fields_arr(2))),
            row.getString(rela_schema.fieldIndex(rel_fields_arr(3)))))
          .map(r => (r._1, r._2, cn.piflow.bundle.util.RedisUtil.getMKFather(r._3, tableName,distinctTableType,jedisCluster.getJedisCluster), r._4))
          .map(i => Row.fromSeq(Array(i._1,i._2,i._3,i._4)))
      var df_backToHiveRelation = spark.sqlContext.createDataFrame(backToHiveRelation, rela_schema)
      jedisCluster.close()
      out.write("Relation", df_backToHiveRelation)
    }
    out.write("Entity", df_backToHive)
  }
}
