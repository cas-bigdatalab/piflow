package cn.piflow.bundle.microorganism

import java.io._
import java.net.URL
import java.text.ParseException
import java.util
import java.util.ArrayList
import java.util.zip.GZIPInputStream

import cn.piflow.bundle.microorganism.util.CustomIOTools
import cn.piflow.bundle.microorganism.util.Process
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroupEnum}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.rdd.RDD
import org.apache.spark.sql.types.{StringType, StructField, StructType}
import org.apache.spark.sql.{DataFrame, Row, SparkSession}
import org.biojava.bio.BioException
import org.elasticsearch.action.bulk.BulkProcessor
import org.json.JSONObject
import org.elasticsearch.action.index.IndexRequest
import org.elasticsearch.spark.sql.EsSparkSQL

import scala.collection.mutable.ArrayBuffer



class GenBankParse extends ConfigurableStop{
  val authorEmail: String = "xiaoxiao@cnic.cn"
  val description: String = "Load file from ftp url."
  val inportList: List[String] = List(PortEnum.NonePort.toString)
  val outportList: List[String] = List(PortEnum.NonePort.toString)


  var es_nodes:String = _   //es的节点，多个用逗号隔开
  var port:String= _           //es的端口好
  var es_index:String = _     //es的索引
  var es_type:String =  _     //es的类型

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val sc = spark.sparkContext
    import spark.sqlContext.implicits._
    import spark.implicits._


    val inDf = in.read()
    inDf.show()
    println("++++++++++++++++++++++++++++++++++++++++++++++++++001")
    inDf.schema.printTreeString()


//    var list2 = new ArrayBuffer[ArrayBuffer[String]]
    var list222 = new ArrayList[ArrayList[String]]

    val rows: Array[Row] = inDf.collect()
    try {
      for (i <- 0 until rows.size) {

        val sourceFile = rows(i)(0).toString
        println("++++++++++++++++++++++++++++++++++++++++++++++++++002" + sourceFile)

        if (sourceFile.endsWith("seq")) {
          println(sourceFile)

          val fileinputStream = new FileInputStream(sourceFile)
          println("Start processing file ----->" + sourceFile)

          val br = new BufferedReader(new InputStreamReader(fileinputStream))

          val sequenceIterator = CustomIOTools.IOTools.readGenbankDNA(br, null)

          var doc: JSONObject = null
          var count = 0


          while (sequenceIterator.hasNext) {
//            var list1 = new ArrayBuffer[String]
            var list001 = new ArrayList[String]

            doc = new JSONObject()
            try {
              var seq = sequenceIterator.nextRichSequence()

              if (seq.getAccession.equals("CP010565")) {
                println(seq.getAccession)
              }

              Process.processSingleSequence(seq, doc)

              println("++++++++++++++++++++++++++++++++++++++++++++++++++" + sourceFile)

              //list1+=(sourceFile)
              // list1+=(seq.getAccession)
              //              list1+=(doc.toString())
              //              list2+=(list1)
              //              println(list1.size+"-----"+list2.size)
              list001.add(doc.toString())
              list001.add(seq.getAccession)
              list222.add(list001)

            }
            catch {
              case e: BioException =>
                e.getMessage
              case e: ParseException =>
                e.printStackTrace()
            }
          }
        }
      }
    } catch {
      case e: FileNotFoundException =>
        e.printStackTrace()
      case e: IOException =>
        e.printStackTrace()
    }


    println("#################")


    var jsonDF: DataFrame = null
    for (i <- 0 until list222.size()) {

//      println("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$" + i)
//      println(list222.get(i).size())
//
//      val esId = list222.get(i).get(1).toString
//      println(esId)

      // 加载 json 字符串 为 df
      val jsonRDD = spark.sparkContext.makeRDD(list222.get(i).get(0).toString() :: Nil)
      jsonDF = spark.read.json(jsonRDD)
      jsonDF.show()
      jsonDF.schema.printTreeString()


      val options = Map("es.index.auto.create"-> "true",
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
    val es_nodes = new PropertyDescriptor().name("es_nodes").displayName("REDIS_HOST").defaultValue("").required(true)
    val port = new PropertyDescriptor().name("port").displayName("PORT").defaultValue("").required(true)
    val es_index = new PropertyDescriptor().name("es_index").displayName("ES_INDEX").defaultValue("").required(true)
    val es_type = new PropertyDescriptor().name("es_type").displayName("ES_TYPE").defaultValue("").required(true)


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
    List(StopGroupEnum.MicroorganismGroup.toString)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }


}
