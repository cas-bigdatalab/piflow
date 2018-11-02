package cn.piflow.bundle.es

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroupEnum}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.SparkSession
import org.elasticsearch.spark.rdd.EsSpark

class QueryEs extends ConfigurableStop {

  override val description: String = "query data with dataframe from elasticSearch "
  val authorEmail: String = "ygang@cnic.cn"
  val inportCount: Int = 0
  val outportCount: Int = 1

  var es_nodes:String = _   //es的节点，多个用逗号隔开
  var port:String= _           //es的端口好
  var es_index:String = _     //es的索引
  var es_type:String =  _     //es的类型
  var field_name:String =  _     //es的类型
  var field_content:String =  _     //es的类型

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val ssc = spark.sqlContext

    // 查询 语句  字段：内容
    val query =
      s"""
         |{
         |  "query":{
         |  "match":{
         |
         |     "${field_name}":"${field_content}"
         |    }
         |  }
         |}
        """.stripMargin

//    val query2 =
//      s"""
//         |{
//         |  "query":{
//         |  "terms":{
//         |
//          |     "age":[22]
//         |    }
//         |  }
//         |}
//        """.stripMargin
//
//    val query3 =
//      s"""
//         |{
//         |  "query":{
//         |  "match":{
//         |     "name":"rose *"
//         |    }
//         |  }
//         |}
//        """.stripMargin


    val options = Map("es.index.auto.create"-> "true",
      "es.nodes.wan.only"->"true",
      "es.query" -> query,
      "es.nodes"->es_nodes,"es.port"->port)


    val outDf = ssc.read.format("org.elasticsearch.spark.sql")
      .options(options).load(s"${es_index}/${es_type}")

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
    field_name=MapUtil.get(map,key="field_name").asInstanceOf[String]
    field_content=MapUtil.get(map,key="field_content").asInstanceOf[String]

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val es_nodes = new PropertyDescriptor().name("es_nodes").displayName("REDIS_HOST").defaultValue("").required(true)
    val port = new PropertyDescriptor().name("port").displayName("PORT").defaultValue("").required(true)
    val es_index = new PropertyDescriptor().name("es_index").displayName("ES_INDEX").defaultValue("").required(true)
    val es_type = new PropertyDescriptor().name("es_type").displayName("ES_TYPE").defaultValue("").required(true)
    val field_name = new PropertyDescriptor().name("field_name").displayName("field_name").defaultValue("").required(true)
    val field_content = new PropertyDescriptor().name("field_content").displayName("field_content").defaultValue("").required(true)


    descriptor = es_nodes :: descriptor
    descriptor = port :: descriptor
    descriptor = es_index :: descriptor
    descriptor = es_type :: descriptor
    descriptor = field_name :: descriptor
    descriptor = field_content :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("es.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroupEnum.ESGroup.toString)
  }


  override val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  override val outportList: List[String] = List(PortEnum.NonePort.toString)
}
