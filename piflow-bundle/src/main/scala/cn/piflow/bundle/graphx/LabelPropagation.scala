package cn.piflow.bundle.graphx

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.graphx._
import org.apache.spark.graphx.lib.LabelPropagation
import org.apache.spark.sql.SparkSession

class LabelPropagation extends ConfigurableStop {

  val authorEmail: String = "06whuxx@163.com"
  val description: String = "Compute sub graphs"
  var edgePortIn : String = "edgesIn"
  var vertexPortIn : String = "vertexIn"
  val inportList: List[String] = List(edgePortIn,vertexPortIn)

  var edgePortOut : String = "edgesOut"
  var vertexPortOut : String = "vertexOut"
  val outportList: List[String] = List(edgePortOut,vertexPortOut)

  var maxIter:String = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val sc=spark.sparkContext
    val edge=in.read(edgePortIn).asInstanceOf[EdgeRDD[Int]]
    val vertex=in.read(vertexPortIn).asInstanceOf[VertexRDD[Int]]
    val graph=Graph(vertex,edge)

    var maxIterValue:Int=50
    if(maxIter!=""){
      maxIterValue=maxIter.toInt
    }

    val res=LabelPropagation.run(graph,maxIterValue)

    import spark.sqlContext.implicits._
    out.write(edgePortOut,res.edges.toDF())
    out.write(vertexPortOut,res.vertices.toDF())
  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  def setProperties(map : Map[String, Any]): Unit = {
    maxIter = MapUtil.get(map,"maxIter").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val maxIter = new PropertyDescriptor()
      .name("maxIter")
      .displayName("MAX_ITER")
      .defaultValue("")
      .allowableValues(Set(""))
      .required(false)
      .example("20")
    descriptor = maxIter :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/graphx/LabelPropagation.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.GraphX)
  }

}
