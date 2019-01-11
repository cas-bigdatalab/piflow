package cn.piflow.bundle.microorganism

import java.io._

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.{DataFrame, SparkSession}
import org.elasticsearch.spark.sql.EsSparkSQL
import org.json.JSONObject


class TaxonomyParse extends ConfigurableStop{
  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "Load file from ftp url."
  val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  val outportList: List[String] = List(PortEnum.NonePort.toString)


  var es_nodes:String = _   //es的节点，多个用逗号隔开
  var port:String= _           //es的端口好
  var es_index:String = _     //es的索引
  var es_type:String =  _     //es的类型

  var filePath:String = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val sc = spark.sparkContext
    val ssc = spark.sqlContext
    println("###############################")

//    val inDf = in.read()
//    inDf.show()
//    inDf.printSchema()
//    val rows: Array[Row] = inDf.collect()
//    val pathDir = new File(rows(0)(0).toString).getParent




    val path = "/ftpTaxonomy1/1/gencode.dmp"
    val pathDir: String = new File(path).getParent
    filePath = pathDir + File.separator + "nodes.dm"

    // #########################################------004 ---namese.dmp
    if (filePath.endsWith("names.dmp")) {

      val optionsFromEs = Map("es.index.auto.create"-> "true",
        "es.nodes.wan.only"->"true",
        "es.nodes"->es_nodes,"es.port"->port)
      //load data with df from es
      val esDf = ssc.read.format("org.elasticsearch.spark.sql").options(optionsFromEs).load(s"${es_index}/${es_type}")


      val br = new BufferedReader(new FileReader(filePath))
      var line: String = null;
      var count = 0
      var divDF :DataFrame = null
      while ((line = br.readLine) != null && line != null) {

        val tokens: Array[String] = line.split("\\t\\|\\t")
        val doc = new JSONObject()
        doc.put("genetic_code_id", tokens(0))
        doc.put("genetic_code_name", tokens(2))
        doc.put("genetic_code_translation_table", tokens(3).trim)
        doc.put("genetic_code_start_codons", tokens(4).replace("\t|","").trim)

        if (count==0) {
          val jsonRDD = spark.sparkContext.makeRDD(doc.toString :: Nil)
          divDF = spark.read.json(jsonRDD)
        } else {
          val jsonRDD = spark.sparkContext.makeRDD(doc.toString :: Nil)
          divDF = spark.read.json(jsonRDD).union(divDF)
        }
        count = count+1
      }

      //      divDF.show()

      val outDf = esDf.join(divDF, Seq("genetic_code_id")).
        filter(esDf.col("genetic_code_id") === divDF.col("genetic_code_id"))

      val optionsToEs = Map("es.index.auto.create" -> "true",
        "es.mapping.id" -> "tax_id",
        "es.nodes" -> es_nodes,
        "es.port" -> port)
      // df 写入 es
      EsSparkSQL.saveToEs(outDf, s"${es_index}/${es_type}", optionsToEs)
      println("nodes.dmp--------------->存储成功")


      filePath = pathDir + File.separator + "names.dmp"
    }





    // #########################################------001 ---nodes.dmp
    if (filePath.endsWith("nodes.dmp")) {
      val br = new BufferedReader(new FileReader(filePath))
      var line: String = null;
      var count =1
      while ((line = br.readLine) != null  &&line != null) {
//        println(count)
        val doc = new JSONObject()
        val tokens: Array[String] = line.split("\\t\\|\\t")
        doc.put("tax_id", tokens(0))
        doc.put("parent_tax_id", tokens(1))
        doc.put("rank", tokens(2))
        doc.put("embl_code", tokens(3))
        doc.put("division_id", tokens(4))
        doc.put("genetic_code_id", tokens(6))
        doc.put("mitochondrial_genetic_code_id", tokens(8))
//        println(doc)
        count = count+1
        if (tokens(0).equals("2492834") ){
          println(tokens(0))
        }
          // 加载 json 字符串 为 df
          val jsonRDD = spark.sparkContext.makeRDD(doc.toString :: Nil)
          val jsonDF = spark.read.json(jsonRDD)

          val options = Map("es.index.auto.create" -> "true",
            "es.mapping.id" -> "tax_id",
            "es.nodes" -> es_nodes, "es.port" -> port)
          // df 写入 es
          EsSparkSQL.saveToEs(jsonDF, s"${es_index}/${es_type}", options)
          println("nodes.dmp--------------->存储成功")


      }
      filePath = pathDir + File.separator + "division.dmp"
    }

    // #########################################------002 ---division.dmp
    else if (filePath.endsWith("division.dmp")) {

      val options = Map("es.index.auto.create"-> "true",
        "es.nodes.wan.only"->"true",
        "es.nodes"->es_nodes,"es.port"->port)

      //load data with df from es
      val esDf = ssc.read.format("org.elasticsearch.spark.sql").options(options).load(s"${es_index}/${es_type}")

      val br = new BufferedReader(new FileReader(filePath))
      var line: String = null;
      var count = 0
      var divDF :DataFrame = null
      while ((line = br.readLine) != null && line != null) {
        val tokens: Array[String] = line.split("\\t\\|\\t")
        val doc = new JSONObject()
        doc.put("division_id", tokens(0))
        doc.put("dive", tokens(1))
        doc.put("diname", tokens(2))
        if (count==0) {
          val jsonRDD = spark.sparkContext.makeRDD(doc.toString :: Nil)
          divDF = spark.read.json(jsonRDD)
        } else {
          val jsonRDD = spark.sparkContext.makeRDD(doc.toString :: Nil)
          divDF = spark.read.json(jsonRDD).union(divDF)
        }
        count = count+1
      }

      val outDf = esDf.join(divDF, Seq("division_id")).filter(esDf.col("division_id") === divDF.col("division_id"))

      val options1 = Map("es.index.auto.create" -> "true",
        "es.mapping.id" -> "tax_id",
        "es.nodes" -> es_nodes,
        "es.port" -> port)
      // df 写入 es
      EsSparkSQL.saveToEs(outDf, s"${es_index}/${es_type}", options1)
      println("nodes.dmp--------------->存储成功")


      filePath = pathDir + File.separator + "gencode.dmp"
    }


    // #########################################------003 ---gencode.dmp
    else if (filePath.endsWith("gencode.dmp")) {

      val optionsFromEs = Map("es.index.auto.create"-> "true",
        "es.nodes.wan.only"->"true",
        "es.nodes"->es_nodes,"es.port"->port)
      //load data with df from es
      val esDf = ssc.read.format("org.elasticsearch.spark.sql").options(optionsFromEs).load(s"${es_index}/${es_type}")


      val br = new BufferedReader(new FileReader(filePath))
      var line: String = null;
      var count = 0
      var divDF :DataFrame = null
      while ((line = br.readLine) != null && line != null) {

        val tokens: Array[String] = line.split("\\t\\|\\t")
        val doc = new JSONObject()
        doc.put("genetic_code_id", tokens(0))
        doc.put("genetic_code_name", tokens(2))
        doc.put("genetic_code_translation_table", tokens(3).trim)
        doc.put("genetic_code_start_codons", tokens(4).replace("\t|","").trim)

        if (count==0) {
          val jsonRDD = spark.sparkContext.makeRDD(doc.toString :: Nil)
          divDF = spark.read.json(jsonRDD)
        } else {
          val jsonRDD = spark.sparkContext.makeRDD(doc.toString :: Nil)
          divDF = spark.read.json(jsonRDD).union(divDF)
        }
        count = count+1
      }

      //      divDF.show()

      val outDf = esDf.join(divDF, Seq("genetic_code_id")).
        filter(esDf.col("genetic_code_id") === divDF.col("genetic_code_id"))

      val optionsToEs = Map("es.index.auto.create" -> "true",
        "es.mapping.id" -> "tax_id",
        "es.nodes" -> es_nodes,
        "es.port" -> port)
      // df 写入 es
      EsSparkSQL.saveToEs(outDf, s"${es_index}/${es_type}", optionsToEs)
      println("nodes.dmp--------------->存储成功")


      filePath = pathDir + File.separator + "names.dmp"
    }





  }

  def processNodes(index:String,types:String)={

  }



  def setProperties(map: Map[String, Any]): Unit = {
    es_nodes=MapUtil.get(map,key="es_nodes").asInstanceOf[String]
    port=MapUtil.get(map,key="port").asInstanceOf[String]
    es_index=MapUtil.get(map,key="es_index").asInstanceOf[String]
    es_type=MapUtil.get(map,key="es_type").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val es_nodes = new PropertyDescriptor().name("es_nodes").displayName("es_nodes").defaultValue("").required(true)
    val port = new PropertyDescriptor().name("port").displayName("port").defaultValue("").required(true)
    val es_index = new PropertyDescriptor().name("es_index").displayName("es_index").defaultValue("").required(true)
    val es_type = new PropertyDescriptor().name("es_type").displayName("es_type").defaultValue("").required(true)


    descriptor = es_nodes :: descriptor
    descriptor = port :: descriptor
    descriptor = es_index :: descriptor
    descriptor = es_type :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("/microorganism/png/Taxonomy.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.MicroorganismGroup.toString)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }


}
