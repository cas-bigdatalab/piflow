package cn.piflow.bundle.jdbc

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Language, Port, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.SparkSession

/**
  * Created by xjzhu@cnic.cn on 7/23/19
  */
class OracleReadByPartition extends ConfigurableStop{
  override val authorEmail: String = "xjzhu@cnic.cn"
  override val description: String = "Read data From oracle"
  override val inportList: List[String] = List(Port.DefaultPort)
  override val outportList: List[String] = List(Port.DefaultPort)

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

    val url=new PropertyDescriptor()
      .name("url")
      .displayName("Url")
      .description("The Url,for example jdbc:oracle:thin:@10.0.86.237:1521/newdb")
      .defaultValue("")
      .required(true)
      .example("jdbc:oracle:thin:@10.0.86.237:1521/newdb")
    descriptor = url :: descriptor

    val user=new PropertyDescriptor()
      .name("user")
      .displayName("User")
      .description("The user name of database")
      .defaultValue("")
      .required(true)
      .example("root")
    descriptor = user :: descriptor

    val password=new PropertyDescriptor()
      .name("password")
      .displayName("Password")
      .description("The password of database")
      .defaultValue("")
      .required(true)
      .example("123456")
      .sensitive(true)
    descriptor = password :: descriptor

    val sql=new PropertyDescriptor()
      .name("sql")
      .displayName("Sql")
      .description("The sql sentence you want to execute")
      .defaultValue("")
      .required(true)
      .language(Language.Sql)
      .example("select * from test")
    descriptor = sql :: descriptor

    val partitionColumn=new PropertyDescriptor()
      .name("partitionColumn")
      .displayName("PartitionColumn")
      .description("partitioned column")
      .defaultValue("")
      .required(true)
      .example("id")
    descriptor = partitionColumn :: descriptor

    val lowerBound=new PropertyDescriptor()
      .name("lowerBound")
      .displayName("LowerBound")
      .description("The lowerbound of partitioned columns")
      .defaultValue("")
      .required(true)
      .example("1")
    descriptor = lowerBound :: descriptor

    val upperBound=new PropertyDescriptor()
      .name("upperBound")
      .displayName("UpperBound")
      .description("The  upperBound of partitioned columns")
      .defaultValue("")
      .required(true)
      .example("20")
    descriptor = upperBound :: descriptor

    val numPartitions=new PropertyDescriptor()
      .name("numPartitions")
      .displayName("NumPartitions")
      .description("The number of partitions ")
      .defaultValue("")
      .required(true)
      .example("5")
    descriptor = numPartitions :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/jdbc/OracleRead.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.JdbcGroup)
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
