package cn.piflow.bundle.nsfc.distinct

import cn.piflow.bundle.util.JedisClusterImplSer
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.types.{StringType, StructField, StructType}
import org.apache.spark.sql.{Column, DataFrame, Row, SparkSession}
import redis.clients.jedis.HostAndPort

class HivePSNDistinct  extends ConfigurableStop{
  override val authorEmail: String = "xiaomeng7890@gmail.com"
  override val description: String = "person table distinct"
  override val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  override val outportList: List[String] = List("Relation", "Entity")

  var tableName : String = _ //after wash
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

  override def setProperties(map: Map[String, Any]): Unit = {
    tableName = MapUtil.get(map,"tableName").asInstanceOf[String]
    idKey = MapUtil.get(map,"idKey").asInstanceOf[String]
    noChange = MapUtil.get(map,"noChange").asInstanceOf[Boolean]
    distinctRule = MapUtil.get(map,"distinctRule").asInstanceOf[String]
    distinctFields = MapUtil.get(map,"distinctFields").asInstanceOf[String]
    primaryKey = MapUtil.get(map,"primaryKey").asInstanceOf[String]
    distinctTableType = MapUtil.get(map,"distinctTableType").asInstanceOf[String]
    rel_fields = MapUtil.get(map,"relFields").asInstanceOf[String]
    used_fields = MapUtil.get(map,"usedFields").asInstanceOf[String]
    redis_server_ip = MapUtil.get(map,"redis ip").asInstanceOf[String]
    redis_server_port = MapUtil.get(map,"redis port").asInstanceOf[Int]
    redis_server_passwd = MapUtil.get(map,"redis passwd").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val tableName = new PropertyDescriptor().
      name("tableName").
      displayName("distinct tablename").
      description("distinct tablename").
      allowableValues(Set("origin.o_stat_prp_persons_full", "temp.t_pj_member")).
      required(true)
    descriptor = tableName :: descriptor

    // afterMap.put("id_hash", (card_code + card_type).##.toString)
    val idKey = new PropertyDescriptor().
      name("idKey").
      displayName("hashed id key").
      description("hashed id key, generated from person id expansion").
      defaultValue("id_hash").
      required(true)
    descriptor = idKey :: descriptor

    val noChange = new PropertyDescriptor().
      name("noChange").
      displayName("noChange").
      description("need process?").
      defaultValue("True").
      allowableValues(Set("True", "False")).
      required(true)

    descriptor = noChange :: descriptor

    val distinctRule = new PropertyDescriptor().
      name("distinctRule").
      displayName("distinct rule").
      description("distinctRule").
      defaultValue("zh_name&email,zh_name&tel").
      required(true)
    descriptor = distinctRule :: descriptor

    val distinctFields = new PropertyDescriptor().
      name("distinctFields").
      displayName("distinctFields").
      description("the fields listed in distinct rule").
      defaultValue("zh_name,email,tel").
      required(true)
    descriptor = distinctFields :: descriptor

    val primaryKey = new PropertyDescriptor().
      name("primaryKey").
      displayName("primaryKey").
      description("the primary key (psn_code)").
      defaultValue("psn_code").
      required(true)
    descriptor = primaryKey :: descriptor

    val distinctTableType = new PropertyDescriptor().
      name("distinctTableType").
      displayName("distinctTableType").
      description("the table name:\n pj for pjmember \nprp for prpmember, for distinct use ").
      defaultValue("pj").
      allowableValues(Set("pj","prp")).
      required(true)
    descriptor = distinctTableType :: descriptor

    val relFields = new PropertyDescriptor().
      name("relFields").
      displayName("relation fields").
      description("relation fields, 3 for pj \n4 for prp").
      defaultValue("id,prj_code,psn_code").
      allowableValues(Set("id,prj_code,psn_code",  "id,prp_code,psn_code,seq_no")).
      required(true)
    descriptor = relFields :: descriptor

    val used_fields = new PropertyDescriptor().
      name("usedFields").
      displayName("all used field").
      description("all used field").
      allowableValues(Set("id,psn_code,zh_name,id_type,id_no,birthday,gender,degree_code,nation,tel,email,org_code,zero,identity_card,military_id,passport,four,home_return_permit,mainland_travel_permit_for_taiwan_residents,source,uuid,id_hash",
        "psn_code,prp_code,zh_name,birthday,email,prof_title,gender,degreecode,regioncode,tel,mobile,zero,identity_card,military_id,passport,four,home_return_permit,mainland_travel_permit_for_taiwan_residents,seq_no,source,uuid,id_hash")).
      required(true)
    descriptor = used_fields :: descriptor

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
