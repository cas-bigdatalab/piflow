package cn.piflow.bundle.es

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.MapUtil
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroupEnum}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.SparkSession
import org.elasticsearch.spark.sql.EsSparkSQL

class QurryEs extends  ConfigurableStop{
  val description: String = "Qurry data from Es."

  override val authorEmail: String = "xiaoxiao@cnic.cn"
  val inportList: List[String] = List(PortEnum.NonePort.toString)
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)

  var es_nodes:String = _   //es的节点，多个用逗号隔开
  var port:Int= _           //es的端口好
  var es_index:String = _     //es的索引
  var es_type:String =  _     //es的类型

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()

    val sc = spark.sqlContext
    //连接es
    val qurry =
      """
        |{
        |  "query":{
        |  "match":{
        |      "id":2
        |    }
        |  }
        |}
      """.stripMargin

    val options = Map("es.index.auto.create"-> "true",
      "es.nodes"->"10.0.86.239","es.port"->"9200")

//    val sdf = sc.read.format("org.elasticsearch.spark.sql").options(options).load("test/test",qurry)

    val df = EsSparkSQL.esDF(sc,"customer/doc",qurry)
    println(df.schema)
    out.write(df)


  }



  def setProperties(map: Map[String, Any]): Unit = {
    es_nodes=MapUtil.get(map,key="es_nodes").asInstanceOf[String]
    port=Integer.parseInt(MapUtil.get(map,key="port").toString)
    es_index=MapUtil.get(map,key="es_index").asInstanceOf[String]
    es_type=MapUtil.get(map,key="es_type").asInstanceOf[String]

    println(es_index)
    println(port)
    println(es_nodes)
    println(es_type)


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




  override def getIcon(): Array[Byte] = ???

  override def getGroup(): List[String] = {
    List(StopGroupEnum.ESGroup.toString)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

}
