package cn.piflow.bundle.ml_clustering

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.ml.clustering.GaussianMixture
import org.apache.spark.sql.SparkSession

class GaussianMixtureTraining extends ConfigurableStop{
  val authorEmail: String = "06whuxx@163.com"
  val description: String = "GaussianMixture clustering"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)
  var training_data_path:String =_
  var model_save_path:String=_
  var k:String=_
  var maxIter:String=_
  var tol:String=_

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()

    //load data stored in libsvm format as a dataframe
    val data=spark.read.format("libsvm").load(training_data_path)

    var kValue:Int=2
    if(k!=""){
      kValue=k.toInt
    }

    //Param for maximum number of iterations (>= 0)
    var maxIterValue:Int=50
    if(maxIter!=""){
      maxIterValue=maxIter.toInt
    }


    var tolValue:Double=0.0001
    if(tol=="online"){
      tolValue=tol.toDouble
    }


    //clustering with GaussianMixture algorithm
    val model=new GaussianMixture()
      .setMaxIter(maxIterValue)
      .setTol(tolValue)
      .setK(kValue)
      .fit(data)

    //model persistence
    model.save(model_save_path)

    import spark.implicits._
    val dfOut=Seq(model_save_path).toDF
    dfOut.show()
    out.write(dfOut)

  }

  def initialize(ctx: ProcessContext): Unit = {

  }


  def setProperties(map: Map[String, Any]): Unit = {
    training_data_path=MapUtil.get(map,key="training_data_path").asInstanceOf[String]
    model_save_path=MapUtil.get(map,key="model_save_path").asInstanceOf[String]
    maxIter=MapUtil.get(map,key="maxIter").asInstanceOf[String]
    k=MapUtil.get(map,key="k").asInstanceOf[String]
    tol=MapUtil.get(map,key="tol").asInstanceOf[String]

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val training_data_path = new PropertyDescriptor().name("training_data_path").displayName("TRAINING_DATA_PATH").defaultValue("").required(true)
    val model_save_path = new PropertyDescriptor().name("model_save_path").displayName("MODEL_SAVE_PATH").description("").defaultValue("").required(true)
    val maxIter=new PropertyDescriptor().name("maxIter").displayName("MAX_ITER").description("Param for maximum number of iterations (>= 0).").defaultValue("").required(false)
    val k=new PropertyDescriptor().name("k").displayName("K").description("Number of independent Gaussians in the mixture model. Must be greater than 1. Default: 2. ").defaultValue("").required(false)
    val tol=new PropertyDescriptor().name("tol").displayName("TOL").description("Param for the convergence tolerance for iterative algorithms (>= 0).").defaultValue("").required(false)
    descriptor = training_data_path :: descriptor
    descriptor = model_save_path :: descriptor
    descriptor = maxIter :: descriptor
    descriptor = tol :: descriptor
    descriptor = k :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/ml_clustering/GaussianMixtureTraining.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.MLGroup.toString)
  }

}
