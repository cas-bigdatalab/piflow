package cn.piflow.bundle.microorganism

import java.io._
import java.net.UnknownHostException
import java.util.ArrayList
import java.util.regex.Pattern

import cn.piflow.bundle.microorganism.util.BioProject
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroupEnum}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.{Row, SparkSession}
import org.elasticsearch.spark.sql.EsSparkSQL
import org.json.{JSONArray, JSONObject, XML}


class BioSampleParse extends ConfigurableStop{
  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "Load file from ftp url."
  val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  val outportList: List[String] = List(PortEnum.NonePort.toString)


  var es_nodes:String = _   //es的节点，多个用逗号隔开
  var port:String= _           //es的端口好
  var es_index:String = _     //es的索引
  var es_type:String =  _     //es的类型

  var docName = "BioSample"

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val sc = spark.sparkContext

    val inDf= in.read()
//    inDf.show()
//    inDf.schema.printTreeString()


    val rows: Array[Row] = inDf.collect()
    for (i <- 0 until rows.size) {

      //   /ftpBioSample1/biosample.xml
      val sourceFile = rows(i)(0).toString
      println("++++++++++++++++++++++++++++++++++++++++++++++++++"+sourceFile)

      var line: String = null
      var xml = ""
      val br: BufferedReader = new BufferedReader(new FileReader(sourceFile))
      br.readLine()
      br.readLine()

      var count = 0
      while ((line = br.readLine()) != null) {
        xml = xml + line
        if (line.indexOf("</" + docName + ">") != -1) {
          count = count + 1

          val doc: JSONObject = XML.toJSONObject(xml).getJSONObject(docName)
          val accession = doc.optString("accession")

          // Attributes
          val attrs: String = doc.optString("Attributes")
          if (attrs.equals("")) {
            doc.remove("Attributes")
          }

          // Links
          val links: String = doc.optString("Links")
          if (links != null) {
            if (links.equals("")) {
              doc.remove("Links")
            }
          }

          val bio = new BioProject

          // owner.name
          val owner = doc.optString("Owner")
          if (owner != null) {
            if (owner.isInstanceOf[JSONArray]) for (k <- 0 until owner.toArray.length) {

              val singleOwner: JSONObject = owner(k).asInstanceOf[JSONObject]
              bio.convertConcrete2KeyVal(singleOwner, "Name")
            }
          }

          // Models.Model
          val models = doc.optJSONObject("Models")
          if (models != null) {
            bio.convertConcrete2KeyVal(models, "Models")
          }


//          if (count < 20) {
            println("#####################################" + count)
            // 加载 json 字符串 为 df
            val jsonRDD = spark.sparkContext.makeRDD(doc.toString() :: Nil)
            val jsonDF = spark.read.json(jsonRDD)
            jsonDF.show()
            //      jsonDF.schema.printTreeString()

            val options = Map("es.index.auto.create" -> "true",
              "es.mapping.id" -> "accession",
              "es.nodes" -> es_nodes, "es.port" -> port)

            // df 写入 es
            EsSparkSQL.saveToEs(jsonDF, s"${es_index}/${es_type}", options)
//          }

          xml = ""
        }
      }

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
    ImageUtil.getImage("bioProject.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroupEnum.MicroorganismGroup.toString)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }


}
