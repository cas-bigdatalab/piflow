package cn.piflow.bundle.ml_clustering

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.ml.clustering.LDA
import org.apache.spark.sql.SparkSession

class LDATraining extends ConfigurableStop{
  val authorEmail: String = "06whuxx@163.com"
  val description: String = "LDA clustering"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)
  var training_data_path:String =_
  var model_save_path:String=_
  var k:Int=_
  var checkpointInterval:Int=_
  var maxIter:String=_
  var docConcentration:String=_
  var optimizer:String=_
  var topicConcentration:String=_

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()

    //load data stored in libsvm format as a dataframe
    val data=spark.read.format("libsvm").load(training_data_path)


    //Param for maximum number of iterations (>= 0)
    var maxIterValue:Int=50
    if(maxIter!=""){
      maxIterValue=maxIter.toInt
    }


    var optimizerValue:String="online"
    if(optimizer!=""){
      optimizerValue=optimizer
    }

    var docConcentrationValue:Double=1/k
    if(optimizer=="online"){
      docConcentrationValue=1/k
    }else{
      docConcentrationValue=50/k+1
    }
    if(docConcentration!=""){
      docConcentrationValue=docConcentration.toDouble
    }

    var topicConcentrationValue:Double=1/k
    if(optimizer=="online"){
      topicConcentrationValue=1/k
    }else{
      topicConcentrationValue=1.1
    }
    if(topicConcentration!=""){
      topicConcentrationValue=topicConcentration.toDouble
    }



    //clustering with LDA algorithm
    val model=new LDA()
      .setMaxIter(maxIterValue)
      .setCheckpointInterval(checkpointInterval)
      .setDocConcentration(docConcentrationValue)
      .setOptimizer(optimizerValue)
      .setTopicConcentration(topicConcentrationValue)
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
    docConcentration=MapUtil.get(map,key="docConcentration").asInstanceOf[String]
    k=Integer.parseInt(MapUtil.get(map,key="k").toString)
    topicConcentration=MapUtil.get(map,key="topicConcentration").asInstanceOf[String]
    optimizer=MapUtil.get(map,key="optimizer").asInstanceOf[String]
    checkpointInterval=Integer.parseInt(MapUtil.get(map,key="checkpointInterval").toString)

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val training_data_path = new PropertyDescriptor().name("training_data_path").displayName("TRAINING_DATA_PATH").defaultValue("").required(true)
    val model_save_path = new PropertyDescriptor().name("model_save_path").displayName("MODEL_SAVE_PATH").description("").defaultValue("").required(true)
    val maxIter=new PropertyDescriptor().name("maxIter").displayName("MAX_ITER").description("Param for maximum number of iterations (>= 0).").defaultValue("").required(false)
    val k=new PropertyDescriptor().name("k").displayName("K").description("The number of topics. ").defaultValue("").required(true)
    val docConcentration=new PropertyDescriptor().name("docConcentration").displayName("DOC_CONCENTRATION").description("Concentration parameter (commonly named \"alpha\") for the prior placed on documents' distributions over topics (\"theta\").").defaultValue("").required(false)
    val topicConcentration=new PropertyDescriptor().name("topicConcentration").displayName("TOPIC_CONCENTRATION").description("Concentration parameter (commonly named \"beta\" or \"eta\") for the prior placed on topics' distributions over terms.").defaultValue("").required(false)
    val checkpointInterval=new PropertyDescriptor().name("checkpointInterval").displayName("CHECK_POINT_INTERVAL").description("Param for set checkpoint interval (>= 1) or disable checkpoint (-1). E.g. 10 means that the cache will get checkpointed every 10 iterations.").defaultValue("").required(true)
    val optimizer=new PropertyDescriptor().name("optimizer").displayName("OPTIMIZER").description("Optimizer or inference algorithm used to estimate the LDA model.").defaultValue("").required(false)
    descriptor = training_data_path :: descriptor
    descriptor = model_save_path :: descriptor
    descriptor = maxIter :: descriptor
    descriptor = docConcentration :: descriptor
    descriptor = topicConcentration :: descriptor
    descriptor = checkpointInterval :: descriptor
    descriptor = optimizer :: descriptor
    descriptor = k :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/ml_clustering/LDATraining.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.MLGroup.toString)
  }

}
