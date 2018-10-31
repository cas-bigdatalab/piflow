package cn.piflow.bundle.es

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroupEnum}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.{SparkConf, SparkContext}
import org.apache.spark.sql.SparkSession
import org.elasticsearch.spark.rdd.EsSpark
import org.elasticsearch.spark.sql.EsSparkSQL

class NewPutEs extends ConfigurableStop {

  override val description: String = "put data with dataframe to elasticSearch "
  val authorEmail: String = "ygang@cnic.cn"
  val inportCount: Int = 0
  val outportCount: Int = 1

  var es_nodes:String = _   //es的节点，多个用逗号隔开
  var port:String= _           //es的端口好
  var es_index:String = _     //es的索引
  var es_type:String =  _     //es的类型

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val inDf = in.read()
    inDf.show()

    val sc = spark.sparkContext
    val options = Map("es.index.auto.create"-> "true",
      "es.nodes"->es_nodes,"es.port"->port)

    EsSparkSQL.saveToEs(inDf,s"${es_index}/${es_type}",options)



    //      val json1 = """{"name":"jack", "age":24, "sex":"man"}"""
    //      val json2 = """{"name":"rose", "age":22, "sex":"woman"}"""
    //
    //      val rddData = sc.makeRDD(Seq(json1, json2))
    //
    //      EsSpark.saveJsonToEs(rddData, "spark/json2",options)
    //自定义id
    // EsSpark.saveJsonToEs(rddData, "spark/json1", Map("es.mapping.id"->"name"))

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
    ImageUtil.getImage("es.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroupEnum.HiveGroup.toString)
  }


  override val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  override val outportList: List[String] = List(PortEnum.NonePort.toString)
}
