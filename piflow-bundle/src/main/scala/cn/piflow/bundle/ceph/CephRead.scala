package cn.piflow.bundle.ceph

import cn.piflow._
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.sql.types.{StringType, StructField, StructType}
import org.apache.spark.sql.{DataFrame, SparkSession}

class CephRead extends ConfigurableStop  {

  val authorEmail: String = "niuzj@gmqil.com"
  val description: String = "Read data from  ceph"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var cephAccessKey:String = _
  var cephSecretKey:String = _
  var cephEndpoint:String = _
  var types: String = _
  var path: String = _
  var header: Boolean = _
  var delimiter: String = _
  var schema: String = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()

    spark.conf.set("fs.s3a.access.key", cephAccessKey)
    spark.conf.set("fs.s3a.secret.key", cephSecretKey)
    spark.conf.set("fs.s3a.endpoint", cephEndpoint)
    spark.conf.set("fs.s3a.connection.ssl.enabled", "false")

    var df:DataFrame = null

    if (types == "parquet") {
      df = spark.read
        .parquet(path)
    }

    if (types == "csv") {
      if (header){
        df = spark.read
          .option("header", header)
          .option("inferSchema", "true")
          .option("delimiter", delimiter)
          .csv(path)
      }
      else{
        val field = schema.split(",").map(x => x.trim)
        val structFieldArray: Array[StructField] = new Array[StructField](field.size)
        for (i <- 0 to field.size - 1) {
          structFieldArray(i) = new StructField(field(i), StringType, nullable = true)
        }
        val schemaStructType = StructType(structFieldArray)

        df = spark.read
          .option("header", header)
          .option("inferSchema", "false")
          .option("delimiter", delimiter)
          .option("timestampFormat", "yyyy/MM/dd HH:mm:ss ZZ")
          .schema(schemaStructType)
          .csv(path)
      }
    }

    if (types == "json") {
      df = spark.read
        .json(path)
    }

    out.write(df)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }



  override def setProperties(map: Map[String, Any]): Unit = {
    cephAccessKey = MapUtil.get(map,"cephAccessKey").asInstanceOf[String]
    cephSecretKey = MapUtil.get(map, "cephSecretKey").asInstanceOf[String]
    cephEndpoint = MapUtil.get(map,"cephEndpoint").asInstanceOf[String]
    types = MapUtil.get(map,"types").asInstanceOf[String]
    path =  MapUtil.get(map,"path").asInstanceOf[String]
    header = MapUtil.get(map, "header").asInstanceOf[String].toBoolean
    delimiter = MapUtil.get(map, "delimiter").asInstanceOf[String]
    schema = MapUtil.get(map, "schema").asInstanceOf[String]
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

    val header = new PropertyDescriptor()
      .name("header")
      .displayName("Header")
      .description("Whether the csv file has a header")
      .defaultValue("false")
      .allowableValues(Set("true", "false"))
      .required(true)
      .example("true")
    descriptor = header :: descriptor

    val delimiter = new PropertyDescriptor()
      .name("delimiter")
      .displayName("Delimiter")
      .description("The delimiter of csv file")
      .defaultValue("")
      .required(true)
      .example(",")
    descriptor = delimiter :: descriptor

    val schema = new PropertyDescriptor()
      .name("schema")
      .displayName("Schema")
      .description("The schema of csv file")
      .defaultValue("")
      .required(false)
      .example("id,name,gender,age")
    descriptor = schema :: descriptor

    val path = new PropertyDescriptor()
      .name("path")
      .displayName("Path")
      .description("The file path you want to write to")
      .defaultValue("")
      .required(true)
      .example("s3a://radosgw-test/test_df")
    descriptor = path :: descriptor


    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/ceph/ceph.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.CephGroup)
  }


}
