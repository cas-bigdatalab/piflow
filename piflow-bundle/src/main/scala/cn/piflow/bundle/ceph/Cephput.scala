package cn.piflow.bundle.ceph


import cn.piflow.conf.ConfigurableStop
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import org.apache.spark.sql.SparkSession

import java.util.Properties
import java.io.{FileInputStream, IOException}


class Cephput extends ConfigurableStop {

  //get config.properties
  val config = new Properties()
  try {
    val configFile = new FileInputStream("config.properties")
    config.load(configFile)
    configFile.close()
  } catch {
    case e: IOException =>
      println(s"Failed to load config.properties file: ${e.getMessage}")
  }

  //  cephAccessKey = "your_ceph_access_key"
  //  cephSecretKey = "your_ceph_secret_key"
  //  cephBucket = "your_ceph_bucket"
  //  cephEndpoint = "your_ceph_endpoint" // Example: "http://ceph-cluster:7480"

  val cephAccessKey = config.getProperty("ceph.accessKey")
  val cephSecretKey = config.getProperty("ceph.secretKey")
  val cephBucket = config.getProperty("ceph.bucket")
  val cephEndpoint = config.getProperty("ceph.domain.ip")


  override val authorEmail: String = "niuzj0@gmail.com"
  override val description: String = "Put data into ceph"
  override val inportList: List[String] = List(Port.DefaultPort)
  override val outportList: List[String] = List(Port.DefaultPort)


  var types: String = _


  override def perform(in: JobInputStream, out: JobOutputStream, pec:JobContext): Unit = {

    // Create a Spark session
    val spark = SparkSession.builder()
      .appName("SparkToCephExample")
      .getOrCreate()


    // Create a DataFrame from the data
    val df = in.read()



    spark.conf.set("fs.s3a.access.key", cephAccessKey)
    spark.conf.set("fs.s3a.secret.key", cephSecretKey)
    spark.conf.set("fs.s3a.endpoint", cephEndpoint)

    // Write the DataFrame to Ceph


    if (types=="parquet") {
      df.write
        .format("parquet") // You can choose the format you prefer (e.g., parquet, ORC, etc.)
        .option("header", "true")
        .mode("overwrite") // You can use "overwrite" or "append" based on your needs
        .save(s"s3a://$cephBucket@$cephEndpoint")
    }
    if (types=="csv") {
      df.write
        .format("csv")
        .option("header", "true")
        .option("delimiter", ",") // CSV文件的分隔符
        .option("quote", "\"") // 引号字符
        .option("escape", "\"") // 转义字符
        .mode("overwrite") // You can use "overwrite" or "append" based on your needs
        .save(s"s3a://$cephBucket@$cephEndpoint")
    }

    if (types=="json") {
    df.write
      .format("json")
      .option("compression", "gzip") // 压缩算法，可选项包括gzip, snappy, lzo, none
      .mode("overwrite") // You can use "overwrite" or "append" based on your needs
      .save(s"s3a://$cephBucket@$cephEndpoint")
    }
    // Stop the Spark session when done
    spark.stop()

  }

  override def setProperties(map: Map[String, Any]): Unit ={
    types = MapUtil.get(map,key="types").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor: List[PropertyDescriptor] = List()

    val types = new PropertyDescriptor()
      .name("types")
      .displayName("Types")
      .description("The format you want to write is json,csv,parquet")
      .defaultValue("csv")
      .allowableValues(Set("json", "csv", "parquet"))
      .required(true)
      .example("csv")
    descriptor = types :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/ceph/ceph.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.CephGroup)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

}
