package cn.piflow.bundle.ceph

import cn.piflow._
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.sql.{DataFrame, SparkSession}


class CephRead extends ConfigurableStop  {

  val authorEmail: String = "niuzj@gmqil.com"
  val description: String = "Read data from  ceph"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var cephAccessKey:String = _
  var cephSecretKey:String = _
  var cephBucket:String = _
  var cephEndpoint:String = _
  var types: String = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()

    spark.conf.set("fs.s3a.access.key", cephAccessKey)
    spark.conf.set("fs.s3a.secret.key", cephSecretKey)
    spark.conf.set("fs.s3a.endpoint", cephEndpoint)

    var df:DataFrame = null

    if (types == "parquet") {
      df = spark.read
        .option("compression", "gzip") // 压缩算法，可选项包括gzip, snappy, lzo, none
        .parquet(s"s3a://$cephBucket@$cephEndpoint")
    }
    if (types == "csv") {
       df = spark.read
        .option("header", true)
        .option("inferSchema", true)
        .option("delimiter", ",")
        .csv(s"s3a://$cephBucket@$cephEndpoint")
    }
    if (types == "json") {
        df = spark.read
        .option("multiline", "true") // 处理多行 JSON
        .json(s"s3a://$cephBucket@$cephEndpoint")
    }

    out.write(df)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }



  override def setProperties(map: Map[String, Any]): Unit = {
    cephAccessKey = MapUtil.get(map,"cephAccessKey").asInstanceOf[String]
    cephSecretKey = MapUtil.get(map, "cephSecretKey").asInstanceOf[String]
    cephBucket = MapUtil.get(map,"cephBucket").asInstanceOf[String]
    cephEndpoint = MapUtil.get(map,"cephEndpoint").asInstanceOf[String]
    types = MapUtil.get(map,"types").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {

    var descriptor : List[PropertyDescriptor] = List()

    val cephAccessKey=new PropertyDescriptor()
      .name("cephAccessKey")
      .displayName("cephAccessKey")
      .description("This parameter is of type String and represents the access key used to authenticate with the Ceph storage system.")
      .defaultValue("")
      .required(true)
      .example("")
    descriptor = cephAccessKey :: descriptor

    val cephSecretKey=new PropertyDescriptor()
      .name("cephSecretKey")
      .displayName("cephSecretKey")
      .description("This parameter is of type String and represents the secret key used to authenticate with the Ceph storage system")
      .defaultValue("")
      .required(true)
      .example("")
    descriptor = cephSecretKey :: descriptor

    val cephBucket=new PropertyDescriptor()
      .name("cephBucket")
      .displayName("cephBucket")
      .description("This parameter is of type String and represents the name of the bucket in the Ceph storage system where the data will be stored/retrieved")
      .defaultValue("")
      .required(true)
      .example("")
    descriptor = cephBucket :: descriptor


    val cephEndpoint = new PropertyDescriptor()
      .name("cephEndpoint")
      .displayName("cephEndpoint")
      .description("This parameter is of type String and represents the endpoint URL of the Ceph storage system. It is used to establish a connection with the Ceph cluster")
      .defaultValue("")
      .required(true)
      .example("http://cephcluster:7480")
      .sensitive(true)
    descriptor = cephEndpoint :: descriptor

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


}
