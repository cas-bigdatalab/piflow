package cn.piflow.bundle.hive

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, Language, Port, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.SparkContext
import org.apache.spark.sql.{DataFrame, Row, SQLContext, SparkSession}

/**
  * HIVE JDBC DRIVER DESIGN FOR HIVE 1.2.1
  */
class SelectHiveQLByJDBC extends ConfigurableStop {
  override val authorEmail: String = "xiaomeng7890@gmail.com"
  override val description: String = "some hive can only achieve by jdbc, this stop is designed for this"
  override val inportList: List[String] = List(Port.DefaultPort)
  override val outportList: List[String] = List(Port.DefaultPort)

  private val driverName = "org.apache.hive.jdbc.HiveDriver"
  var hiveUser : String = _
  var hivePassword : String = _
  var jdbcUrl : String = _
  var sql : String = _

  override def setProperties(map: Map[String, Any]): Unit = {

    hiveUser = MapUtil.get(map,"hiveUser").asInstanceOf[String]
    hivePassword = MapUtil.get(map,"hivePassword").asInstanceOf[String]
    jdbcUrl = MapUtil.get(map,"jdbcUrl").asInstanceOf[String]
    sql = MapUtil.get(map,"sql").asInstanceOf[String]
  }
   override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val hiveUser = new PropertyDescriptor()
      .name("hiveUser")
      .displayName("hiveUser")
      .description("Users connected to hive")
      .defaultValue("root")
      .required(true)
      .example("root")

    descriptor = hiveUser :: descriptor

    val hivePassword = new PropertyDescriptor().
      name("hivePassword")
      .displayName("hivePassword")
      .description("Password connected to hive")
      .defaultValue("123456")
      .required(true)
      .example("123456")
      .sensitive(true)
    descriptor = hivePassword :: descriptor

    val jdbcUrl = new PropertyDescriptor().
      name("jdbcUrl")
      .displayName("jdbcUrl")
      .description("URL for hive to connect to JDBC")
      .defaultValue("jdbc:hive2://packone12:2181,packone13:2181,packone11:2181/middle;serviceDiscoveryMode=zooKeeper;zooKeeperNamespace=hiveserver2")
      .required(true)
      .example("jdbc:hive2://127.0.0.1:2181/newdb")
    descriptor = jdbcUrl :: descriptor

    val sql = new PropertyDescriptor().
      name("query")
      .displayName("Hive Query")
      .description("SQL query statement of hive")
      .defaultValue("")
      .required(true)
      .language(Language.Sql)
      .example("select * from test.user1")
     descriptor = sql :: descriptor

    descriptor
  }


  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/hive/SelectHiveQLByJdbc.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.HiveGroup)
  }


  override def initialize(ctx: ProcessContext): Unit = {}

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val sc = pec.get[SparkSession]()
    val df = getDF (sc.sqlContext, sc.sparkContext, sql)
    out.write(df)
  }

  def getDF(sqlContext : SQLContext, sc : SparkContext, tableName : String) : DataFrame = {
    var df = sqlContext.sql(sql)
    val count = df.count()
    if (count == 0) {
      println("Cant read by normal read, using JDBC <== this will cost a lot of time")
      df = getJDBCDF(sqlContext, sc, tableName)
    }
    df
  }

  def getJDBCDF(sqlContext : SQLContext, sc : SparkContext, tableName : String) : DataFrame = {
    import java.sql.DriverManager
    try
      Class.forName(driverName)
    catch {
      case e: ClassNotFoundException =>
        e.printStackTrace()
        System.exit(1)
    }
    val conn = DriverManager.getConnection(jdbcUrl, hiveUser, hivePassword)
    val ptsm = conn.prepareStatement(sql)
    println(ptsm)
    val rs = ptsm.executeQuery()
    var rows = Seq[Row]()
    val meta = rs.getMetaData
    for (i <- 1 to meta.getColumnCount) {
      println(meta.getColumnName(i))
    }
    while (rs.next) {
      var row = Seq[String]()
      for (i <- 1 to meta.getColumnCount) {
        row = row.:+(rs.getString(i))
      }
      rows = rows.:+(Row.fromSeq(row))
    }
    val organizationRDD = sc.makeRDD(rows)
    sqlContext.createDataFrame(organizationRDD, sqlContext.read.table(tableName).schema)
  }
}
