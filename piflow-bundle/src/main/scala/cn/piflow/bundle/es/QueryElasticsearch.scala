package cn.piflow.bundle.es

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.SparkSession

class QueryElasticsearch extends ConfigurableStop {

  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "Query data from Elasticsearch"
  val inportList: List[String] = List(Port.NonePort)
  val outportList: List[String] = List(Port.DefaultPort)

  var es_nodes : String =  _
  var es_port  : String  =  _
  var es_index : String =  _
  var es_type  : String  =  _
  var jsonDSL  : String  =  _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val ssc = spark.sqlContext

    val options = Map("es.index.auto.create"-> "true",
      "es.nodes.wan.only"->"true",
      "es.query" -> jsonDSL,
      "es.nodes"->es_nodes,"es.port"->es_port)

    val outDf = ssc.read.format("org.elasticsearch.spark.sql")
      .options(options).load(s"${es_index}/${es_type}")

    out.write(outDf)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  def setProperties(map : Map[String, Any]): Unit = {
    es_nodes=MapUtil.get(map,key="es_nodes").asInstanceOf[String]
    es_port=MapUtil.get(map,key="es_port").asInstanceOf[String]
    es_index=MapUtil.get(map,key="es_index").asInstanceOf[String]
    es_type=MapUtil.get(map,key="es_type").asInstanceOf[String]
    jsonDSL=MapUtil.get(map,key="jsonDSL").asInstanceOf[String]

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val es_nodes = new PropertyDescriptor()
      .name("es_nodes")
      .displayName("Es_Nodes")
      .description("Node of Elasticsearch")
      .defaultValue("")
      .required(true)
      .example("")
    descriptor = es_nodes :: descriptor

    val es_port = new PropertyDescriptor()
      .name("es_port")
      .displayName("Es_Port")
      .description("Port of Elasticsearch")
      .defaultValue("9200")
      .required(true)
      .example("")
    descriptor = es_port :: descriptor

    val es_index = new PropertyDescriptor()
      .name("es_index")
      .displayName("Es_Index")
      .description("Index of Elasticsearch")
      .defaultValue("")
      .required(true)
      .example("")
    descriptor = es_index :: descriptor

    val es_type = new PropertyDescriptor()
      .name("es_type")
      .displayName("Es_Type")
      .description("Type of Elasticsearch")
      .defaultValue("")
      .required(true)
      .example("")
    descriptor = es_type :: descriptor

    val jsonDSL = new PropertyDescriptor()
      .name("jsonDSL")
      .displayName("JsonDSL")
      .description("DSL of Elasticsearch")
      .defaultValue("")
      .required(true)
      .example("GET _search \n {\\\"query\\\":{\\\"match_all:{}\\\"}}")
    descriptor = jsonDSL :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/elasticsearch/QueryEs.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.ESGroup)
  }
}
