package cn.piflow.bundle.unstructured
import cn.piflow.conf.util.ProcessUtil
import cn.piflow.util.UnstructuredUtils
import org.apache.spark.sql.types.{ArrayType, MapType, StringType, StructType}
import org.apache.spark.sql.{SparkSession, functions}

import scala.collection.mutable.ArrayBuffer
object test {
  def main(args: Array[String]): Unit = {
    val spark = SparkSession.builder()
      .master("local[*]")
      .appName("MaxMinNormalizationTest")
      .config("spark.driver.memory", "1g")
      .config("spark.executor.memory", "2g")
      .config("spark.cores.max", "2")
      .getOrCreate()
    spark.conf.set("spark.sql.decimalType.precision", "38")

    val fileSource = "nfs"
    val filePath = "D:/work/0.πFlow/2.集成unstruct-io/1.测试文件/pdf;D:/work/0.πFlow/2.集成unstruct-io/1.测试文件/full_text.pdf"
    val strategy = "auto"
    val unstructuredHost: String = "10.0.82.194"
    val unstructuredPort: String = "8000"
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
        println(s"local path:$path")
        curlCommandParams += "-F"
        curlCommandParams += s"files=@$path"
      }
    }
    if ("nfs".equals(fileSource)) {
      val fileList = UnstructuredUtils.getLocalFilePaths(filePath)
      fileListSize = fileList.size
      fileList.foreach { path =>
        println(s"local path:$path")
        curlCommandParams += "-F"
        curlCommandParams += s"files=@$path"
      }
    }
    val (output, error): (String, String) = ProcessUtil.executeCommand(curlCommandParams.toSeq)
    if (output.nonEmpty) {
      println(output)
      import spark.implicits._
      if (fileListSize > 1) {
        val schema1 = ArrayType(
          new StructType()
            .add("type", StringType)
            .add("element_id", StringType)
            .add("text", StringType)
            .add("metadata", MapType(StringType, StringType))
        )
        val df = Seq(output).toDS().toDF("json").withColumn("data", functions.from_json($"json", schema1))
        //        val df = spark.read.json(Seq(output).toDS())
        //          .withColumn("data", functions.explode($"value"))
        //          .select("data.*")
        df.show(10)
      } else {
        //        val schema2 = new StructType()
        //          .add("type", StringType)
        //          .add("element_id", StringType)
        //          .add("text", StringType)
        //          .add("metadata", MapType(StringType, StringType))
        //        val df = Seq(output).toDS().toDF("json").withColumn("data", functions.from_json($"json", schema2)).
        val df = spark.read.json(Seq(output).toDS())
        df.show(10)
      }
    } else {
      println(s"########## Exception: $error")
      throw new Exception(s"########## Exception: $error")
    }
  }

//  def test()={
//    val spark = SparkSession.builder()
//      .appName("JsonArrayToDataFrame")
//      .config("spark.master", "local")
//      .getOrCreate()
//
//    // 用于示例的 JSON 数组字符串
//    val exampleJsonArrayString1 =
//      """[[{"type":"UncategorizedText","element_id":"48f89b630677c2cbb70e2ba05bf7a363","text":"454","metadata":{"languages":["eng"],"page_number":1,"filename":"embedded-images-tables.pdf","filetype":"application/pdf"}},{"type":"Header","element_id":"9ca201e648ed74cfc838b6661f59addf","text":"O. Sanni, A.P.I. Popoola / Data in Brief 22 (2019) 451–457","metadata":{"languages":["eng"],"page_number":1,"filename":"embedded-images-tables.pdf","filetype":"application/pdf"}},{"type":"UncategorizedText","element_id":"f0e5c879f7d220552d8ad5b3503bd038","text":"Fig. 4. Anodic and cathodic polarization curve of stainless steel in 0.5 M H2SO4 solution in the presence and absence of ES.","metadata":{"languages":["eng"],"page_number":1,"parent_id":"9ca201e648ed74cfc838b6661f59addf","filename":"embedded-images-tables.pdf","filetype":"application/pdf"}}],[{"type":"UncategorizedText","element_id":"d54c69149058772f0dbffe267619fe62","text":"ExoFlow: A Universal Workflow System for Exactly-Once DAGs Siyuan Zhuang, UC Berkeley; Stephanie Wang, UC Berkeley and Anyscale; Eric Liang and Yi Cheng, Anyscale; Ion Stoica, UC Berkeley","metadata":{"languages":["eng"],"page_number":1,"filename":"full_text.pdf","filetype":"application/pdf"}},{"type":"Title","element_id":"566b36175e2c048f6f7288b4b6d2792e","text":"https://www.usenix.org/conference/osdi23/presentation/zhuang","metadata":{"languages":["eng"],"page_number":1,"filename":"full_text.pdf","filetype":"application/pdf"}},{"type":"Title","element_id":"416fdc1b946e9213121dcc2f87fc632d","text":"ExoFlow: A Universal Workflow System for Exactly-Once DAGs","metadata":{"languages":["eng"],"page_number":2,"filename":"full_text.pdf","filetype":"application/pdf"}}]]
//      """
//
//    // 用于示例的第二种 JSON 数组字符串
//    val exampleJsonArrayString2 =
//      """[{"type":"UncategorizedText","element_id":"48f89b630677c2cbb70e2ba05bf7a363","text":"454","metadata":{"languages":["eng"],"page_number":1,"filename":"embedded-images-tables.pdf","filetype":"application/pdf"}},{"type":"Header","element_id":"9ca201e648ed74cfc838b6661f59addf","text":"O. Sanni, A.P.I. Popoola / Data in Brief 22 (2019) 451–457","metadata":{"languages":["eng"],"page_number":1,"filename":"embedded-images-tables.pdf","filetype":"application/pdf"}},{"type":"UncategorizedText","element_id":"f0e5c879f7d220552d8ad5b3503bd038","text":"Fig. 4. Anodic and cathodic polarization curve of stainless steel in 0.5 M H2SO4 solution in the presence and absence of ES.","metadata":{"languages":["eng"],"page_number":1,"parent_id":"9ca201e648ed74cfc838b6661f59addf","filename":"embedded-images-tables.pdf","filetype":"application/pdf"}}]
//      """
//
//    val exampleSchema = new StructType()
//      .add("type", StringType)
//      .add("element_id", StringType)
//      .add("text", StringType)
//      .add("metadata", MapType(StringType, StringType))
//
//    import spark.implicits._
//
//    // 将第一种格式的 JSON 数组字符串转换为 DataFrame
//    val df1 = spark.read.json(Seq(exampleJsonArrayString1).toDS())
//      .withColumn("data", functions.explode($"value"))
//      .select("data.*")
//
//    // 将第二种格式的 JSON 数组字符串转换为 DataFrame
//    val df2 = spark.read.json(Seq(exampleJsonArrayString2).toDS())
//
//    // 将两个 DataFrame 合并为一个
//    val combinedDF = df1.union(df2)
//
//    combinedDF.show(false)
//  }

}
