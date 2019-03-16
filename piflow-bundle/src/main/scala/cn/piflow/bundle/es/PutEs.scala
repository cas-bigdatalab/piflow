package cn.piflow.bundle.es

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.SparkSession
import org.elasticsearch.spark.sql.EsSparkSQL

class PutEs extends ConfigurableStop {

  override val description: String = "Put data to Elasticsearch "
  val authorEmail: String = "ygang@cnic.cn"

  override val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  override val outportList: List[String] = List(PortEnum.NonePort.toString)

  var es_nodes : String =  _
  var es_port  : String  =  _
  var es_index : String =  _
  var es_type  : String  =  _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val inDf = in.read()

    val sc = spark.sparkContext
    val options = Map("es.index.auto.create"-> "true",
      "es.nodes"->es_nodes,
      "es.port"->es_port)

    EsSparkSQL.saveToEs(inDf,s"${es_index}/${es_type}",options)

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
    val es_nodes = new PropertyDescriptor().name("es_nodes").displayName("es_nodes").defaultValue("Node of Elasticsearch").required(true)
    val es_port = new PropertyDescriptor().name("es_port").displayName("es_port").defaultValue("Port of Elasticsearch").required(true)
    val es_index = new PropertyDescriptor().name("es_index").displayName("es_index").defaultValue("Index of Elasticsearch").required(true)
    val es_type = new PropertyDescriptor().name("es_type").displayName("es_type").defaultValue("Type of Elasticsearch").required(true)


    descriptor = es_nodes :: descriptor
    descriptor = es_port :: descriptor
    descriptor = es_index :: descriptor
    descriptor = es_type :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/elasticsearch/PutEs.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.ESGroup.toString)
  }

}
