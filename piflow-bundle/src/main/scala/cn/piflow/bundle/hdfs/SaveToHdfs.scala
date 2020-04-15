package cn.piflow.bundle.hdfs

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.{FileStatus, FileSystem, Path}
import org.apache.spark.rdd.RDD
import org.apache.spark.sql.types.{StringType, StructField, StructType}
import org.apache.spark.sql.{DataFrame, Row, SaveMode, SparkSession}

import scala.collection.mutable.ArrayBuffer


class SaveToHdfs extends ConfigurableStop {

  val authorEmail: String = "ygang@cnic.cn"
  override val description: String = "Put data into hdfs "
  override val inportList: List[String] = List(Port.DefaultPort)
  override val outportList: List[String] = List(Port.DefaultPort)

  var hdfsDirPath :String= _
  var hdfsUrl :String= _
  var fileName :String = _
  var types :String= _
  var delimiter :String = _
  var header: Boolean = _

  var pathARR:ArrayBuffer[String]=ArrayBuffer()
  var oldFilePath:String = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val hdfsDir =  hdfsUrl+hdfsDirPath

    val config = new Configuration()
    config.set("fs.defaultFS",hdfsUrl)
    val fs = FileSystem.get(config)

    val inDF = in.read()


    if (types=="json"){
      inDF.repartition(1).write.json(hdfsDir)
    } else if (types=="csv"){
      inDF.repartition(1)
        .write
        .format("csv")
        .mode(SaveMode.Overwrite)
        .option("header", header)
        .option("delimiter",delimiter)
        .save(hdfsDir)
    } else {
      //parquet
      inDF.repartition(1).write.text(hdfsDir)
    }

    iterationFile(hdfsDir)

    val oldPath = new Path(oldFilePath)
    val newPath = new Path(hdfsDir+"/"+fileName)
    fs.rename(oldPath,newPath)


    val rows: List[Row] = pathARR.map(each => {
      var arr:Array[String]=Array(each)
      val row: Row = Row.fromSeq(arr)
      row
    }).toList

    val rowRDD: RDD[Row] = spark.sparkContext.makeRDD(rows)

    val schema: StructType = StructType(Array(
      StructField("path",StringType)
    ))
    val outDF: DataFrame = spark.createDataFrame(rowRDD,schema)

    out.write(outDF)
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
        iterationFile(fsPath)
      } else{
        if (f.getPath.toString.contains("part")){
          pathARR += hdfsUrl+hdfsDirPath+"/"+fileName
          oldFilePath = f.getPath.toString
        }
      }
    }

  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  def setProperties(map : Map[String, Any]): Unit = {
    hdfsUrl = MapUtil.get(map,key="hdfsUrl").asInstanceOf[String]
    hdfsDirPath = MapUtil.get(map,key="hdfsDirPath").asInstanceOf[String]
    fileName = MapUtil.get(map,key="fileName").asInstanceOf[String]
    types = MapUtil.get(map,key="types").asInstanceOf[String]
    delimiter = MapUtil.get(map,key="delimiter").asInstanceOf[String]
    header = MapUtil.get(map,"header").asInstanceOf[String].toBoolean


  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val hdfsDirPath = new PropertyDescriptor()
      .name("hdfsDirPath")
      .displayName("HdfsDirPath")
      .defaultValue("")
      .description("File dir path of HDFS")
      .required(true)
      .example("/work/")
    descriptor = hdfsDirPath :: descriptor

    val hdfsUrl = new PropertyDescriptor()
      .name("hdfsUrl")
      .displayName("HdfsUrl")
      .defaultValue("")
      .description("URL address of HDFS")
      .required(true)
      .example("hdfs://192.168.3.138:8020")
    descriptor = hdfsUrl :: descriptor

    val fileName = new PropertyDescriptor()
      .name("fileName")
      .displayName("FileName")
      .description("File name")
      .defaultValue("")
      .required(true)
      .example("test.csv")
    descriptor = fileName :: descriptor

    val types = new PropertyDescriptor()
      .name("types")
      .displayName("json,csv,text")
      .description("The format you want to write is json,csv,parquet")
      .defaultValue("csv")
      .allowableValues(Set("json","csv","text"))
      .required(true)
      .example("csv")
    descriptor = types :: descriptor

    val delimiter = new PropertyDescriptor()
      .name("delimiter")
      .displayName("delimiter")
      .description("Please set the separator for the type of csv file")
      .defaultValue(",")
      .required(true)
      .example(",")
    descriptor = delimiter :: descriptor

    val header = new PropertyDescriptor()
      .name("header")
      .displayName("header")
      .description("Does the csv file have a header")
      .defaultValue("true")
      .required(true)
        .example("true")
    descriptor = header :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/hdfs/PutHdfs.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.HdfsGroup)
  }

}

