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
  override val description: String = "fetch data with dataframe from elasticSearch "


  var es_nodes:String = _   //es的节点，多个用逗号隔开
  var port:String= _           //es的端口好
  var es_index:String = _     //es的索引
  var es_type:String =  _     //es的类型

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()

    val ssc = spark.sqlContext

    val options = Map("es.index.auto.create"-> "true","es.nodes.wan.only"->"true",
      "es.nodes"->es_nodes,"es.port"->port)

    //load data with df  from es
    val outDf = ssc.read.format("org.elasticsearch.spark.sql").options(options).load(s"${es_index}/${es_type}")
    outDf.show()
    out.write(outDf)

  }
  def initialize(ctx: ProcessContext): Unit = {

  }

  def setProperties(map : Map[String, Any]): Unit = {
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
    ImageUtil.getImage("es.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.ESGroup.toString)
  }



}
