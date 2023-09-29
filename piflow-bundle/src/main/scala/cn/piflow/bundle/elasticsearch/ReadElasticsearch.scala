package cn.piflow.bundle.elasticsearch

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.SparkSession

class ReadElasticsearch extends ConfigurableStop {

  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "Query data from Elasticsearch"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var es_nodes : String =  _
  var es_port  : String  =  _
  var es_index : String =  _
  var es_type  : String  =  _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()

    val esDF = spark.read.format("org.elasticsearch.spark.sql")
      .option("es.nodes", es_nodes)
      .option("es.port", es_port)
      .load(s"${es_index}/${es_type}")

    out.write(esDF)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  def setProperties(map : Map[String, Any]): Unit = {
    es_nodes=MapUtil.get(map,key="es_nodes").asInstanceOf[String]
    es_port=MapUtil.get(map,key="es_port").asInstanceOf[String]
    es_index=MapUtil.get(map,key="es_index").asInstanceOf[String]
    es_type=MapUtil.get(map,key="es_type").asInstanceOf[String]

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val es_nodes = new PropertyDescriptor()
      .name("es_nodes")
      .displayName("Es_Nodes")
      .description("Node of Elasticsearch")
      .defaultValue("")
      .required(true)
      .example("10.0.88.70")
    descriptor = es_nodes :: descriptor

    val es_port = new PropertyDescriptor()
      .name("es_port")
      .displayName("Es_Port")
      .description("Port of Elasticsearch")
      .defaultValue("9200")
      .required(true)
      .example("9200")
    descriptor = es_port :: descriptor

    val es_index = new PropertyDescriptor()
      .name("es_index")
      .displayName("Es_Index")
      .description("Index of Elasticsearch")
      .defaultValue("")
      .required(true)
      .example("test")
    descriptor = es_index :: descriptor

    val es_type = new PropertyDescriptor()
      .name("es_type")
      .displayName("Es_Type")
      .description("Type of Elasticsearch")
      .defaultValue("")
      .required(true)
      .example("test")
    descriptor = es_type :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/elasticsearch/QueryEs.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.ESGroup)
  }
}
