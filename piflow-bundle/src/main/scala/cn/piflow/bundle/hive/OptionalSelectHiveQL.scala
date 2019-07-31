package cn.piflow.bundle.hive

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, PortEnum}
import cn.piflow.conf.bean.PropertyDescriptor
import org.apache.spark.SparkContext
import org.apache.spark.sql.{DataFrame, Row, SQLContext}

class OptionalSelectHiveQL extends ConfigurableStop {
  override val authorEmail: String = "xiaomeng7890@gmail.com"
  override val description: String = "some hive can only achieve by jdbc, this stop is designed for this"
  override val inportList: List[String] = List(PortEnum.NonePort)
  override val outportList: List[String] = List(PortEnum.DefaultPort)

  private val driverName = "org.apache.hive.jdbc.HiveDriver"
  var hiveUser : String = _
  var hivePasswd : String = _
  var jdbcUrl : String = _

  override def setProperties(map: Map[String, Any]): Unit = ???

  override def getPropertyDescriptor(): List[PropertyDescriptor] = ???

  override def getIcon(): Array[Byte] = ???

  override def getGroup(): List[String] = ???

  override def initialize(ctx: ProcessContext): Unit = ???

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = ???

  def getDF(sqlContext : SQLContext, sc : SparkContext, tableName : String) : DataFrame = {
    var df = sqlContext.read.table(tableName)
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
    val conn = DriverManager.getConnection(jdbcUrl, "hive", "123456")
    val ptsm = conn.prepareStatement("select * from " + tableName)
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
