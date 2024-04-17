package cn.piflow.bundle.unstructured

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil, ProcessUtil}
import cn.piflow.conf.{ConfigurableStop, Port}
import cn.piflow.util.UnstructuredUtils
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.SparkSession

import scala.collection.mutable.ArrayBuffer

class HtmlParser extends ConfigurableStop {
  val authorEmail: String = "tianyao@cnic.cn"
  val description: String = "parse html to structured data."
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var filePath: String = _
  var fileSource: String = _


  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()

    val unstructuredHost: String = UnstructuredUtils.unstructuredHost()
    val unstructuredPort: String = UnstructuredUtils.unstructuredPort()
    if (unstructuredHost == null || unstructuredHost.isEmpty) {
      println("########## Exception: can not parse, unstructured host is null!!!")
      throw new Exception("########## Exception: can not parse, unstructured host is null!!!")
    } else if ("127.0.0.1".equals(unstructuredHost) || "localhost".equals(unstructuredHost)) {
      println("########## Exception: can not parse, the unstructured host cannot be set to localhost!!!")
      throw new Exception("########## Exception: can not parse, the unstructured host cannot be set to localhost!!!")
    }
    var localDir = ""
    if ("hdfs".equals(fileSource)) {
      //Download the file to the location,
      localDir = UnstructuredUtils.downloadFilesFromHdfs(filePath)
    }

    //Create a mutable ArrayBuffer to store the parameters of the curl command
    println("curl start==========================================================================")
    val curlCommandParams = new ArrayBuffer[String]()
    curlCommandParams += "curl"
    curlCommandParams += "-X"
    curlCommandParams += "POST"
    curlCommandParams += s"$unstructuredHost:$unstructuredPort/general/v0/general"
    curlCommandParams += "-H"
    curlCommandParams += "accept: application/json"
    curlCommandParams += "-H"
    curlCommandParams += "Content-Type: multipart/form-data"
    if ("hdfs".equals(fileSource)) {
      val fileList = UnstructuredUtils.getLocalFilePaths(localDir)
      fileList.foreach { path =>
        curlCommandParams += "-F"
        curlCommandParams += s"files=@$path"
      }
    }
    if ("nfs".equals(fileSource)) {
      val fileList = UnstructuredUtils.getLocalFilePaths(filePath)
      fileList.foreach { path =>
        curlCommandParams += "-F"
        curlCommandParams += s"files=@$path"
      }
    }
    val (output, error): (String, String) = ProcessUtil.executeCommand(curlCommandParams.toSeq)
    if (output.nonEmpty) {
      println(output)
      val jsonRDD = spark.sparkContext.parallelize(Seq(output))
      val df = spark.read.json(jsonRDD)
      df.show(10)
      out.write(df)
    } else {
      println(s"########## Exception: $error")
      throw new Exception(s"########## Exception: $error")
    }
    //delete local temp file
    if ("hdfs".equals(fileSource)) {
      UnstructuredUtils.deleteTempFiles(localDir)
    }
  }

  override def setProperties(map: Map[String, Any]): Unit = {
    filePath = MapUtil.get(map, "filePath").asInstanceOf[String]
    fileSource = MapUtil.get(map, "fileSource").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor: List[PropertyDescriptor] = List()
    val filePath = new PropertyDescriptor()
      .name("filePath")
      .displayName("FilePath")
      .description("The path of the file(.html/.htm)")
      .defaultValue("/test/test.html")
      .required(true)
      .example("/test/test.html")
    descriptor = descriptor :+ filePath

    val fileSource = new PropertyDescriptor()
      .name("fileSource")
      .displayName("FileSource")
      .description("The source of the file ")
      .defaultValue("hdfs")
      .allowableValues(Set("hdfs", "nfs"))
      .required(true)
      .example("hdfs")
    descriptor = descriptor :+ fileSource

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/unstructured/HtmlParser.png", this.getClass.getName)
  }

  override def getGroup(): List[String] = {
    List("unstructured")
  }


  override def initialize(ctx: ProcessContext): Unit = {

  }

}
