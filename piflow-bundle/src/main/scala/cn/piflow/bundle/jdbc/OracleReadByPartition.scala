package cn.piflow.bundle.jdbc

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.SparkSession

/**
  * Created by xjzhu@cnic.cn on 7/23/19
  */
class OracleReadByPartition extends ConfigurableStop{
  override val authorEmail: String = "xjzhu@cnic.cn"
  override val description: String = "Read data From oracle"
  override val inportList: List[String] = List(PortEnum.DefaultPort)
  override val outportList: List[String] = List(PortEnum.DefaultPort)

  var url:String = _
  var user:String = _
  var password:String = _
  var sql:String = _
  var partitionColumn:String= _
  var lowerBound:Long= _
  var upperBound:Long = _
  var numPartitions:Int = _

  override def setProperties(map: Map[String, Any]): Unit = {
    url = MapUtil.get(map,"url").asInstanceOf[String]
    user = MapUtil.get(map,"user").asInstanceOf[String]
    password = MapUtil.get(map,"password").asInstanceOf[String]
    sql = MapUtil.get(map,"sql").asInstanceOf[String]
    partitionColumn = MapUtil.get(map,"partitionColumn").asInstanceOf[String]
    lowerBound = MapUtil.get(map,"lowerBound").asInstanceOf[String].toLong
    upperBound = MapUtil.get(map,"upperBound").asInstanceOf[String].toLong
    numPartitions = MapUtil.get(map,"numPartitions").asInstanceOf[String].toInt
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val url=new PropertyDescriptor().name("url").displayName("url").description("The Url, for example jdbc:mysql://127.0.0.1/dbname").defaultValue("").required(true)
    descriptor = url :: descriptor

    val user=new PropertyDescriptor().name("user").displayName("user").description("The user name of database").defaultValue("").required(true)
    descriptor = user :: descriptor

    val password=new PropertyDescriptor().name("password").displayName("password").description("The password of database").defaultValue("").required(true)
    descriptor = password :: descriptor

    val sql=new PropertyDescriptor().name("sql").displayName("sql").description("The sql sentence you want to execute").defaultValue("").required(true)
    descriptor = sql :: descriptor

    val partitionColumn=new PropertyDescriptor().name("partitionColumn").displayName("partitionColumn").description("The  partitionby column").defaultValue("").required(true)
    descriptor = partitionColumn :: descriptor

    val lowerBound=new PropertyDescriptor().name("lowerBound").displayName("lowerBound").description("The  lowerBound of partitioned column").defaultValue("").required(true)
    descriptor = lowerBound :: descriptor

    val upperBound=new PropertyDescriptor().name("upperBound").displayName("upperBound").description("The  upperBound of partitioned column").defaultValue("").required(true)
    descriptor = upperBound :: descriptor

    val numPartitions=new PropertyDescriptor().name("numPartitions").displayName("numPartitions").description("The  number of partitions ").defaultValue("").required(true)
    descriptor = numPartitions :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/jdbc/jdbcRead.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.JdbcGroup.toString)
  }

  override def initialize(ctx: ProcessContext): Unit = {}

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val dbtable = "( "  + sql + ")temp"
    val jdbcDF = spark.read.format("jdbc")
      .option("url", url)
      .option("driver", "oracle.jdbc.OracleDriver")
      .option("dbtable", dbtable)
      .option("user", user)
      .option("password",password)
      .option("partitionColumn",partitionColumn)
      .option("lowerBound",lowerBound)
      .option("upperBound",upperBound)
      .option("numPartitions",numPartitions)
      .load()

    out.write(jdbcDF)
  }
}
