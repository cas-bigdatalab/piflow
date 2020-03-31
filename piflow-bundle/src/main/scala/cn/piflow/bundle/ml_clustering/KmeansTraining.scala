package cn.piflow.bundle.ml_clustering

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.ml.clustering.KMeans
import org.apache.spark.sql.SparkSession

class KmeansTraining extends ConfigurableStop{
  val authorEmail: String = "06whuxx@163.com"
  val description: String = "Kmeans clustering"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)
  var training_data_path:String =_
  var model_save_path:String=_
  var maxIter:String=_
  var k:Int=_
  var minTol:String=_


  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()

    //load data stored in libsvm format as a dataframe
    val data=spark.read.format("libsvm").load(training_data_path)


    //Param for maximum number of iterations (>= 0)
    var maxIterValue:Int=50
    if(maxIter!=""){
      maxIterValue=maxIter.toInt
    }

    //Param for the convergence tolerance for iterative algorithms (>= 0).
    var minTolValue:Double=1E-6
    if(minTol!=""){
      minTolValue=minTol.toDouble
    }


    //clustering with kmeans algorithm
    val model=new KMeans()
      .setMaxIter(maxIterValue)
      .setTol(minTolValue)
      .setK(k)
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
    minTol=MapUtil.get(map,key="minTol").asInstanceOf[String]
    k=Integer.parseInt(MapUtil.get(map,key="k").toString)
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val training_data_path = new PropertyDescriptor().name("training_data_path").displayName("TRAINING_DATA_PATH").defaultValue("").required(true)
    val model_save_path = new PropertyDescriptor().name("model_save_path").displayName("MODEL_SAVE_PATH").description("").defaultValue("").required(true)
    val maxIter=new PropertyDescriptor().name("maxIter").displayName("MAX_ITER").description("Param for maximum number of iterations (>= 0).").defaultValue("").required(false)
    val minTol=new PropertyDescriptor().name("minTol").displayName("MIN_TOL").description("Param for the convergence tolerance for iterative algorithms (>= 0).").defaultValue("").required(false)
    val k=new PropertyDescriptor().name("k").displayName("K").description("The number of clusters. ").defaultValue("").required(true)
    descriptor = training_data_path :: descriptor
    descriptor = model_save_path :: descriptor
    descriptor = maxIter :: descriptor
    descriptor = minTol :: descriptor
    descriptor = k :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/ml_clustering/KmeansTraining.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.MLGroup.toString)
  }

}
