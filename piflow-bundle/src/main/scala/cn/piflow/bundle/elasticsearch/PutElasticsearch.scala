package cn.piflow.bundle.elasticsearch

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.SparkSession

class PutElasticsearch extends ConfigurableStop {

  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "Put data into Elasticsearch"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var es_nodes : String =  _
  var es_port  : String  =  _
  var es_index : String =  _
  var es_type  : String  =  _
  var saveMode : String = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val inDfES = in.read()

    inDfES.write.format("org.elasticsearch.spark.sql")
      .option("es.nodes", es_nodes)
      .option("es.port", es_port)
      .option("es.resource", s"${es_index}/${es_type}")
      .mode(saveMode)
      .save()

  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  def setProperties(map : Map[String, Any]): Unit = {
    es_nodes=MapUtil.get(map,key="es_nodes").asInstanceOf[String]
    es_port=MapUtil.get(map,key="es_port").asInstanceOf[String]
    es_index=MapUtil.get(map,key="es_index").asInstanceOf[String]
    es_type=MapUtil.get(map,key="es_type").asInstanceOf[String]
    saveMode=MapUtil.get(map,key="saveMode").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val es_nodes = new PropertyDescriptor()
      .name("es_nodes")
      .displayName("es_nodes")
      .description("Node of Elasticsearch")
      .defaultValue("")
      .required(true)
      .example("10.0.88.70")
    descriptor = es_nodes :: descriptor

    val es_port = new PropertyDescriptor()
      .defaultValue("9200")
      .name("es_port")
      .displayName("es_port")
      .description("Port of Elasticsearch")
      .defaultValue("9200")
      .required(true)
      .example("9200")
    descriptor = es_port :: descriptor

    val es_index = new PropertyDescriptor()
      .name("es_index")
      .displayName("es_index")
      .description("Index of Elasticsearch")
      .defaultValue("")
      .required(true)
      .example("spark")
    descriptor = es_index :: descriptor

    val es_type = new PropertyDescriptor()
      .name("es_type")
      .displayName("es_type")
      .description("Type of Elasticsearch")
      .defaultValue("")
      .required(true)
      .example("testStudent1")
    descriptor = es_type :: descriptor

    val saveMode = new PropertyDescriptor()
      .name("saveMode")
      .displayName("SaveMode")
      .description("save mode")
//      .allowableValues(Set("Append","Overwrite","ErrorIfExists","Ignore"))
      .defaultValue("Overwrite")
      .required(true)
      .example("Overwrite")
    descriptor = saveMode :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/elasticsearch/PutEs.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.ESGroup)
  }

}
