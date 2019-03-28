package cn.piflow.bundle.es

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.SparkSession


class FetchEs extends ConfigurableStop {

  val authorEmail: String = "ygang@cnic.cn"

  override val inportList: List[String] = List(PortEnum.NonePort.toString)
  override val outportList: List[String] = List(PortEnum.DefaultPort.toString)
  override val description: String = "Fetch data from Elasticsearch"

  var es_nodes : String =  _
  var es_port  : String  =  _
  var es_index : String =  _
  var es_type  : String  =  _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()

    val ssc = spark.sqlContext

    val options = Map("es.index.auto.create"-> "true",
      "es.nodes.wan.only"->"true",
      "es.nodes"->es_nodes,
      "es.port"->es_port)

    //load data with df  from es
    val outDf = ssc.read.format("org.elasticsearch.spark.sql").options(options).load(s"${es_index}/${es_type}")
    out.write(outDf)

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
    val es_nodes = new PropertyDescriptor().name("es_nodes").displayName("es_nodes")
      .description("Node of Elasticsearch").defaultValue("").required(true)
    val es_port = new PropertyDescriptor().defaultValue("9200").name("es_port").displayName("es_port")
      .description("Port of Elasticsearch").required(true)
    val es_index = new PropertyDescriptor().name("es_index").displayName("es_index")
      .description("Index of Elasticsearch").defaultValue("").required(true)
    val es_type = new PropertyDescriptor().name("es_type").displayName("es_type")
      .description("Type of Elasticsearch").defaultValue("").required(true)


    descriptor = es_nodes :: descriptor
    descriptor = es_port :: descriptor
    descriptor = es_index :: descriptor
    descriptor = es_type :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/elasticsearch/FetchEs.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.ESGroup.toString)
  }



}
