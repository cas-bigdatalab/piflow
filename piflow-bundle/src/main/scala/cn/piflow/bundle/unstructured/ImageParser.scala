package cn.piflow.bundle.unstructured

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil, ProcessUtil}
import cn.piflow.conf.{ConfigurableStop, Port}
import cn.piflow.util.UnstructuredUtils
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import com.alibaba.fastjson2.{JSON, JSONArray}
import org.apache.spark.sql.{DataFrame, SparkSession}

import scala.collection.mutable.ArrayBuffer

class ImageParser extends ConfigurableStop {
  val authorEmail: String = "tianyao@cnic.cn"
  val description: String = "parse image to structured data."
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var filePath: String = _
  var fileSource: String = _
  var strategy: String = _

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
    curlCommandParams += "-F"
    curlCommandParams += "pdf_infer_table_structure=false"
    curlCommandParams += "-F"
    curlCommandParams += s"strategy=$strategy"
    curlCommandParams += "-F"
    curlCommandParams += "hi_res_model_name=detectron2_lp"
    var fileListSize = 0;
    if ("hdfs".equals(fileSource)) {
      val fileList = UnstructuredUtils.getLocalFilePaths(localDir)
      fileListSize = fileList.size
      fileList.foreach { path =>
        curlCommandParams += "-F"
        curlCommandParams += s"files=@$path"
      }
    }
    if ("nfs".equals(fileSource)) {
      val fileList = UnstructuredUtils.getLocalFilePaths(filePath)
      fileListSize = fileList.size
      fileList.foreach { path =>
        curlCommandParams += "-F"
        curlCommandParams += s"files=@$path"
      }
    }
    val (output, error): (String, String) = ProcessUtil.executeCommand(curlCommandParams.toSeq)
    if (output.nonEmpty) {
      //      println(output)
      import spark.implicits._
      if (fileListSize > 1) {
        val array: JSONArray = JSON.parseArray(output)
        var combinedDF: DataFrame = null
        array.forEach {
          o =>
            val jsonString = o.toString
            val df = spark.read.json(Seq(jsonString).toDS)
            if (combinedDF == null) {
              combinedDF = df
            } else {
              combinedDF = combinedDF.union(df)
            }
        }
        combinedDF.show(10)
        out.write(combinedDF)
      } else {
        val df = spark.read.json(Seq(output).toDS())
        df.show(10)
        out.write(df)
      }
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
    strategy = MapUtil.get(map, "strategy").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor: List[PropertyDescriptor] = List()
    val filePath = new PropertyDescriptor()
      .name("filePath")
      .displayName("FilePath")
      .description("The path of the file(.png/.jpg/.jpeg/.tiff/.bmp/.heic)")
      .defaultValue("/test/test.png")
      .required(true)
      .example("/test/test.png")
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

    val strategy = new PropertyDescriptor()
      .name("strategy")
      .displayName("strategy")
      .description("The method the method that will be used to process the file ")
      .defaultValue("ocr_only")
      .allowableValues(Set("ocr_only"))
      .required(true)
      .example("ocr_only")
    descriptor = descriptor :+ strategy

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/unstructured/ImageParser.png", this.getClass.getName)
  }

  override def getGroup(): List[String] = {
    List("unstructured")
  }


  override def initialize(ctx: ProcessContext): Unit = {

  }

}
