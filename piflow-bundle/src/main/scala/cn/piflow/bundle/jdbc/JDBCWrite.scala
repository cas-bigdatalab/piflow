package cn.piflow.bundle.jdbc

import java.util.Properties

import cn.piflow._
import cn.piflow.conf.ConfigurableStop
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.MapUtil
import org.apache.spark.sql.{SaveMode, SparkSession}

class JDBCWrite extends ConfigurableStop{

  var url:String = _
  var user:String = _
  var password:String = _
  var dbtable:String = _
  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val jdbcDF = in.read()
    val properties = new Properties()
    properties.put("user", user)
    properties.put("password", password)
    jdbcDF.write.mode(SaveMode.Append).jdbc(url,dbtable,properties)
    jdbcDF.show(10)
    out.write(jdbcDF)

  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  override def setProperties(map: Map[String, Any]): Unit = {
    url = MapUtil.get(map,"url").asInstanceOf[String]
    user = MapUtil.get(map,"user").asInstanceOf[String]
    password = MapUtil.get(map,"password").asInstanceOf[String]
    dbtable = MapUtil.get(map,"dbtable").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = ???
}
