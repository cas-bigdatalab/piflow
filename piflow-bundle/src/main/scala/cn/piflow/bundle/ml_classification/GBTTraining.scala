package cn.piflow.bundle.ml_classification

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.ml.classification.GBTClassifier
import org.apache.spark.sql.SparkSession

class GBTTraining extends ConfigurableStop{
  val authorEmail: String = "06whuxx@163.com"
  val description: String = "Train a GBT Model"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)
  var training_data_path:String =_
  var model_save_path:String=_
  var maxBins:String=_
  var maxDepth:String=_
  var minInfoGain:String=_
  var minInstancesPerNode:String=_
  var impurity:String=_
  var subSamplingRate:String=_
  var lossType:String=_
  var stepSize:String=_

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()

    //load data stored in libsvm format as a dataframe
    val data=spark.read.format("libsvm").load(training_data_path)

    //Maximum number of bins used for discretizing continuous features and for choosing how to split on features at each node. More bins give higher granularity.Must be >= 2 and >= number of categories in any categorical feature.
    var maxBinsValue:Int=40
    if(maxBins!=""){
      maxBinsValue=maxBins.toInt
    }

    //Maximum depth of the tree (>= 0).The maximum is 30.
    var maxDepthValue:Int=30
    if(maxDepth!=""){
      maxDepthValue=maxDepth.toInt
    }

    //Minimum information gain for a split to be considered at a tree node.
    var minInfoGainValue:Double=0.2
    if(minInfoGain!=""){
      minInfoGainValue=minInfoGain.toDouble
    }

    //Minimum number of instances each child must have after split.
    var minInstancesPerNodeValue:Int=3
    if(minInstancesPerNode!=""){
      minInstancesPerNodeValue=minInstancesPerNode.toInt
    }

    //Param for the name of family which is a description of the label distribution to be used in the model
    var impurityValue="gini"
    if(impurity!=""){
      impurityValue=impurity
    }

    var subSamplingRateValue:Double=0.6
    if(subSamplingRate!=""){
      subSamplingRateValue=subSamplingRate.toDouble
    }

    var lossTypeValue="logistic"
    if(lossType!=""){
      lossTypeValue=lossType
    }

    var stepSizeValue:Double=0.1
    if(stepSize!=""){
      stepSizeValue=stepSize.toDouble
    }

    //training a GBT model
    val model=new GBTClassifier()
      .setMaxBins(maxBinsValue)
      .setMaxDepth(maxDepthValue)
      .setMinInfoGain(minInfoGainValue)
      .setMinInstancesPerNode(minInstancesPerNodeValue)
      .setImpurity(impurityValue)
      .setLossType(lossTypeValue)
      .setSubsamplingRate(subSamplingRateValue)
      .setStepSize(stepSizeValue)
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
    maxBins=MapUtil.get(map,key="maxBins").asInstanceOf[String]
    maxDepth=MapUtil.get(map,key="maxDepth").asInstanceOf[String]
    minInfoGain=MapUtil.get(map,key="minInfoGain").asInstanceOf[String]
    minInstancesPerNode=MapUtil.get(map,key="minInstancesPerNode").asInstanceOf[String]
    impurity=MapUtil.get(map,key="impurity").asInstanceOf[String]
    subSamplingRate=MapUtil.get(map,key="subSamplingRate").asInstanceOf[String]
    lossType=MapUtil.get(map,key="lossType").asInstanceOf[String]
    stepSize=MapUtil.get(map,key="stepSize").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val training_data_path = new PropertyDescriptor().name("training_data_path").displayName("TRAINING_DATA_PATH").defaultValue("").required(true)
    val model_save_path = new PropertyDescriptor().name("model_save_path").displayName("MODEL_SAVE_PATH").description("").defaultValue("").required(true)
    val maxBins=new PropertyDescriptor().name("maxBins").displayName("MAX_BINS").description("Maximum number of bins used for discretizing continuous features and for choosing how to split on features at each node.").defaultValue("").required(false)
    val maxDepth=new PropertyDescriptor().name("maxDepth").displayName("MAX_DEPTH").description("Maximum depth of the tree").defaultValue("").required(false)
    val minInfoGain=new PropertyDescriptor().name("minInfoGain").displayName("MIN_INFO_GAIN").description("Minimum information gain for a split to be considered at a tree node").defaultValue("").required(false)
    val minInstancesPerNode=new PropertyDescriptor().name("minInstancesPerNode").displayName("MIN_INSTANCES_PER_NODE").description("Minimum number of instances each child must have after split.").defaultValue("").required(false)
    val impurity=new PropertyDescriptor().name("impurity").displayName("IMPURITY").description("Criterion used for information gain calculation (case-insensitive). Supported: \"entropy\" and \"gini\". (default = gini)").defaultValue("").required(false)
    val subSamplingRate=new PropertyDescriptor().name("subSamplingRate").displayName("SUB_SAMPLING_RATE").description("Fraction of the training data used for learning each decision tree, in range (0, 1].").defaultValue("").required(false)
    val lossType=new PropertyDescriptor().name("lossType").displayName("LOSS_TYPE").description("Loss function which GBT tries to minimize. (case-insensitive) Supported: \"logistic\" (default = logistic)").defaultValue("").required(false)
    val stepSize=new PropertyDescriptor().name("stepSize").displayName("STEP_SIZE").description("Param for Step size (a.k.a. learning rate) in interval (0, 1] for shrinking the contribution of each estimator. (default = 0.1)").defaultValue("").required(false)
    descriptor = training_data_path :: descriptor
    descriptor = model_save_path :: descriptor
    descriptor = maxBins :: descriptor
    descriptor = maxDepth :: descriptor
    descriptor = minInfoGain :: descriptor
    descriptor = minInstancesPerNode :: descriptor
    descriptor = impurity :: descriptor
    descriptor = subSamplingRate::descriptor
    descriptor = lossType :: descriptor
    descriptor = stepSize :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/ml_classification/GBTTraining.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.MLGroup.toString)
  }

}
