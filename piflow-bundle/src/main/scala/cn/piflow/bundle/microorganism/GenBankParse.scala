package cn.piflow.bundle.microorganism

import java.io._
import java.text.ParseException
import java.util.ArrayList

import cn.piflow.bundle.microorganism.util.{CustomIOTools, Process}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.{DataFrame, Row, SparkSession}
import org.biojava.bio.BioException
import org.elasticsearch.spark.sql.EsSparkSQL
import org.json.JSONObject


class GenBankParse extends ConfigurableStop{
  val authorEmail: String = "ygang@cnic.cn"
  val description: String = " Parse genbank date put to elasticSearch"
  val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  val outportList: List[String] = List(PortEnum.NonePort.toString)


  var es_nodes:String = _   //es的节点，多个用逗号隔开
  var port:String= _           //es的端口好
  var es_index:String = _     //es的索引
  var es_type:String =  _     //es的类型

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val sc = spark.sparkContext


    val inDf = in.read()
    //inDf.show()
    println("++++++++++++++++++++++++++++++++++++++++++++++++++001")
    println(inDf.count())
    inDf.schema.printTreeString()

    var listSeq = new ArrayList[ArrayList[String]]

    val rows: Array[Row] = inDf.collect()
    try {
      for (i <- 0 until rows.size) {

        val sourceFile = rows(i)(0)
        println("++++++++++++++++++++++++++++++++++++++++++++++++++002" + sourceFile)
        // 字节数组反序列化 为 ByteArrayInputStream
        val bis:ByteArrayInputStream=new ByteArrayInputStream(sourceFile.asInstanceOf[Array[Byte]])

        //val fileinputStream = new FileInputStream(sourceFile)
        val br = new BufferedReader(new InputStreamReader(bis))

        //  解析seq  文件 的字节流
        val sequenceIterator = CustomIOTools.IOTools.readGenbankDNA(br, null)

        var doc: JSONObject = null
        var count = 0
        while (sequenceIterator.hasNext) {
          var listJson = new ArrayList[String]
          doc = new JSONObject()
          try {
            var seq = sequenceIterator.nextRichSequence()

            Process.processSingleSequence(seq, doc)
            // json 字符串
            listJson.add(doc.toString())
            // 序列号  CP009630
            listJson.add(seq.getAccession)

            listSeq.add(listJson)

          }
          catch {
            case e: BioException =>
              e.getMessage
            case e: ParseException =>
              e.printStackTrace()
          }
        }
      }
    } catch {
      case e: FileNotFoundException =>
        e.printStackTrace()
      case e: IOException =>
        e.printStackTrace()
    }

    var jsonDF: DataFrame = null
    for (i <- 0 until listSeq.size()) {

      println("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$" + i)
      //
      println(listSeq.get(i).size())

      // seq 文件中的 json 字符串
      val jsonString = listSeq.get(i).get(0)

      // 序列号  CP009630
      val esId = listSeq.get(i).get(1).toString
      println(esId)

      // 加载 json 字符串 为 df
      val jsonRDD = spark.sparkContext.makeRDD(jsonString.toString() :: Nil)
      jsonDF = spark.read.json(jsonRDD)
      jsonDF.show()
      //      jsonDF.schema.printTreeString()


      val options = Map("es.index.auto.create"-> "true",
        // "es.mapping.id"->"Accession",
        "es.nodes"->es_nodes,"es.port"->port)

      // df 写入 es
      EsSparkSQL.saveToEs(jsonDF,s"${es_index}/${es_type}",options)

    }
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
    ImageUtil.getImage("genbank.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.MicroorganismGroup.toString)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }


}
