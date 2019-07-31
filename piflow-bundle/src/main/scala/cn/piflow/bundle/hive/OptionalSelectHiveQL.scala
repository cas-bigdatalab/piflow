package cn.piflow.bundle.hive

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.SparkContext
import org.apache.spark.sql.{DataFrame, Row, SQLContext, SparkSession}

/**
  * HIVE JDBC DRIVER DESIGN FOR HIVE 1.2.1
  */
class OptionalSelectHiveQL extends ConfigurableStop {
  override val authorEmail: String = "xiaomeng7890@gmail.com"
  override val description: String = "some hive can only achieve by jdbc, this stop is designed for this"
  override val inportList: List[String] = List(PortEnum.NonePort)
  override val outportList: List[String] = List(PortEnum.DefaultPort)

  private val driverName = "org.apache.hive.jdbc.HiveDriver"
  var hiveUser : String = _
  var hivePasswd : String = _
  var jdbcUrl : String = _
  var sql : String = _

  override def setProperties(map: Map[String, Any]): Unit = {
    hiveUser = MapUtil.get(map,"hive user").asInstanceOf[String]
    hivePasswd = MapUtil.get(map,"hive passwd").asInstanceOf[String]
    jdbcUrl = MapUtil.get(map,"jdbcUrl").asInstanceOf[String]
    sql = MapUtil.get(map,"query").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val hiveUser = new PropertyDescriptor().
      name("hive user").
      displayName("hive user").
      description("hive user name").
      defaultValue("hdfs").
      required(true)
    descriptor = hiveUser :: descriptor

    val hivePasswd = new PropertyDescriptor().
      name("hive passwd").
      displayName("hive passwd").
      description("hive password").
      defaultValue("123456").
      required(true)
    descriptor = hivePasswd :: descriptor

    val jdbcUrl = new PropertyDescriptor().
      name("jdbcUrl").
      displayName("jdbcUrl").
      description("hive jdbc url").
      defaultValue("jdbc:hive2://packone12:2181,packone13:2181,packone11:2181/middle;serviceDiscoveryMode=zooKeeper;zooKeeperNamespace=hiveserver2").
      required(true)
    descriptor = jdbcUrl :: descriptor

    val sql = new PropertyDescriptor().
      name("query").
      displayName("hive query").
      description("hive sql query").
      defaultValue("select * from middle.m_person").
      required(true)
    descriptor = sql :: descriptor

    descriptor
  }



  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/hive/PutHiveQL.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.HiveGroup.toString)
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
    val conn = DriverManager.getConnection(jdbcUrl, hiveUser, hivePasswd)
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
