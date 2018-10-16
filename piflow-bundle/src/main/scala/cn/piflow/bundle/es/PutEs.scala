package cn.piflow.bundle.es

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.MapUtil
import cn.piflow.conf.{ConfigurableStop, StopGroupEnum}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.SparkSession
import org.elasticsearch.spark.sql.EsSparkSQL

class PutEs extends ConfigurableStop{
  val description: String = "Put data to Es."

  override val authorEmail: String = "xiaoxiao@cnic.cn"
  override val inportCount: Int = 0
  override val outportCount: Int = 1

  var es_nodes:String = _   //es的节点，多个用逗号隔开
  var port:Int= _           //es的端口好
  var es_index:String = _     //es的索引
  var es_type:String =  _     //es的类型

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {



    val spark = pec.get[SparkSession]()



//    val options = Map("es.index.auto.create"-> "true",
//      "es.nodes"->"10.0.86.239","es.port"->"9200")
//
//    val conf = new SparkConf()
//      .set("spark.driver.allowMultipleContexts", "true")
//
//    conf.set("es.nodes", "10.0.86.239")
//      .set("es.port", "9200")
//      .set("es.index.auto.create", "true")



    val sc = spark.sqlContext

    val inDF = in.read()
    inDF.show()

    println(inDF.schema)

    //连接es
    EsSparkSQL.saveToEs(inDF,"/test/test5")

    println("cunchuchenggong")

  }



  def setProperties(map: Map[String, Any]): Unit = {
    es_nodes=MapUtil.get(map,key="es_nodes").asInstanceOf[String]
    port=Integer.parseInt(MapUtil.get(map,key="port").toString)
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




  override def getIcon(): Array[Byte] = ???

  override def getGroup(): List[String] = {
    List(StopGroupEnum.ESGroup.toString)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }


}
