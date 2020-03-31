package cn.piflow.bundle.neo4j

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.{FileStatus, FileSystem, Path}
import org.apache.spark.sql.{DataFrame, SaveMode, SparkSession}
import org.neo4j.driver.v1._

import scala.collection.mutable.ArrayBuffer

class HiveToNeo4j extends ConfigurableStop{
  override val authorEmail: String = "anhong12@cnic.cn"
  override val description: String = "Hive to Neo4j"
  override val inportList: List[String] =List(Port.DefaultPort)
  override val outportList: List[String] = List(Port.DefaultPort)

  var hiveQL:String = _


  var hdfsDirPath :String= _
  var hdfsUrl :String= _
  var fileName :String = _
  var delimiter :String = _
  var header: Boolean = _

  var pathARR:ArrayBuffer[String]=ArrayBuffer()
  var oldFilePath:String = _

  var url : String =_
  var userName : String =_
  var password : String =_
  var cypher : String =""

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    //selectHiveQL-----------------------------
    val spark = pec.get[SparkSession]()
    println("Select HiveQL started !!!!!!!!!!!!!!!!!!!")
    import spark.sql
    val df = sql(hiveQL)
    println("Select HiveQL done !!!!!!!!!!!!!!!!!!!!!")
    //AllfieldsClean-------------------------

    println("All Fields cleaning started !!!!!!!!!!!!!!!!!!!!!!!!!!!f")
    df.createOrReplaceTempView("temp")

    // clean authors
    spark.sqlContext.udf.register("cleanFields", (fieldStr: String) => {
      if (fieldStr == null) null
      else fieldStr.replaceAll("\"", "")
    })


    val fieldNames: Array[String] = df.schema.fieldNames
    val sqlStringBuilder = new StringBuilder
    for (i <- 0 until fieldNames.length) {
      sqlStringBuilder.append("cleanFields(" + fieldNames(i) + ") as "+fieldNames(i) +",")
    }

    val sqlString = sqlStringBuilder.dropRight(1).toString()

    val frame: DataFrame = spark.sql("select   "+sqlString +"   from temp")

    println("All Fields Cleaned!!!!!!!!!!!!!!!!!!!!")


//frame   now is cleaned data
    //CSVSaveToHDFS----------------------------------

    println("save csv file started !!!!!!!!!!!!!!!!!!!!!!!!!!!")
    val hdfsDir =  hdfsUrl+hdfsDirPath

    val config = new Configuration()
    config.set("fs.defaultFS",hdfsUrl)
    val fs = FileSystem.get(config)

    frame.repartition(1)
      .write
      .format("csv")
      .mode(SaveMode.Overwrite)
      .option("header", header)
      .option("delimiter",delimiter)
      .save(hdfsDir)

    iterationFile(hdfsDir)

    val oldPath = new Path(oldFilePath)
    val newPath = new Path(hdfsDir+"/"+fileName)
    fs.rename(oldPath,newPath)


    println("csv file has been written to HDFS!!!!!!!!!!!!!!!!!!!! ")

    //RunCypherLoadCSV----------------------------------------
    println("run cypher !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    val cqls: Array[String] = cypher.split(";")
    var driver: Driver = GraphDatabase.driver(url, AuthTokens.basic(userName, password))
    var session: Session = null

    try {
      session = driver.session()
      cqls.foreach(eachCql => {
        session.run(eachCql)
      })
    } finally {
      session.close()
      driver.close()
    }

    println("load csv done!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

  }

  // recursively traverse the folder
  def iterationFile(path: String):Unit = {

    val config = new Configuration()
    config.set("fs.defaultFS",hdfsUrl)
    val fs = FileSystem.get(config)

    val listf = new Path(path)

    val statuses: Array[FileStatus] = fs.listStatus(listf)

    for (f <- statuses) {
      val fsPath = f.getPath().toString
      if (f.isDirectory) {
        //        pathARR += fsPath
        iterationFile(fsPath)
      } else{
        if (f.getPath.toString.contains("part")){
          pathARR += hdfsUrl+hdfsDirPath+"/"+fileName
          oldFilePath = f.getPath.toString
        }
      }
    }

  }

  override def setProperties(map: Map[String, Any]): Unit = {
    hiveQL = MapUtil.get(map,"hiveQL").asInstanceOf[String]
    hdfsUrl = MapUtil.get(map,key="hdfsUrl").asInstanceOf[String]
    hdfsDirPath = MapUtil.get(map,key="hdfsDirPath").asInstanceOf[String]
    fileName = MapUtil.get(map,key="fileName").asInstanceOf[String]
    delimiter = MapUtil.get(map,key="delimiter").asInstanceOf[String]
    header = MapUtil.get(map,"header").asInstanceOf[String].toBoolean
    url = MapUtil.get(map,"url").asInstanceOf[String]
    userName = MapUtil.get(map,"userName").asInstanceOf[String]
    password = MapUtil.get(map,"password").asInstanceOf[String]
    cypher = MapUtil.get(map,"cypher").asInstanceOf[String]
}

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val hiveQL = new PropertyDescriptor()
      .name("hiveQL")
      .displayName("HiveQL")
      .defaultValue("")
      .required(true)
      .example("")

    val hdfsDirPath = new PropertyDescriptor()
      .name("hdfsDirPath")
      .displayName("HdfsDirPath")
      .defaultValue("/piflow-CSV-of-Neo4j/xxxxx")
      .required(true)
      .example("")

    val hdfsUrl = new PropertyDescriptor()
      .name("hdfsUrl")
      .displayName("HdfsUrl")
      .defaultValue("hdfs://192.168.3.138:8020")
      .required(true)
      .example("")

    val fileName = new PropertyDescriptor()
      .name("fileName")
      .displayName("FileName")
      .defaultValue("")
      .required(true)
      .example("")

    val delimiter = new PropertyDescriptor()
      .name("delimiter")
      .displayName("Delimiter")
      .description("type is csv ,please set it ")
      .defaultValue("¤")
      .required(true)
      .example("")

    //header
    val header = new PropertyDescriptor()
      .name("header")
      .displayName("Header")
      .description("Whether the csv file have header or not")
      .defaultValue("true")
      .allowableValues(Set("true", "false"))
      .required(true)
      .example("")

    val url=new PropertyDescriptor()
      .name("url")
      .displayName("Url")
      .description("for example bolt://0.0.1.1:7687")
      .defaultValue("bolt://127.0.0.1:7687")
      .required(true)
      .example("")

    val userName=new PropertyDescriptor()
      .name("userName")
      .displayName("UserName")
      .description("the user")
      .defaultValue("neo4j")
      .required(true)
      .example("")

    val password=new PropertyDescriptor()
      .name("password")
      .displayName("Password")
      .description("the password")
      .defaultValue("")
      .required(true)
      .example("")

    val cypher=new PropertyDescriptor()
      .name("cypher")
      .displayName("Cypher")
      .description(" the Cypher")
      .defaultValue("")
      .required(true)
      .example("")


    descriptor = hiveQL :: descriptor
    descriptor = hdfsUrl :: descriptor
    descriptor = hdfsDirPath :: descriptor
    descriptor = fileName :: descriptor
    descriptor = header :: descriptor
    descriptor = delimiter :: descriptor

    descriptor = url :: descriptor
    descriptor = userName :: descriptor
    descriptor = password :: descriptor
    descriptor = cypher :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/neo4j/HiveToNeo4j.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.Neo4jGroup)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }
}
