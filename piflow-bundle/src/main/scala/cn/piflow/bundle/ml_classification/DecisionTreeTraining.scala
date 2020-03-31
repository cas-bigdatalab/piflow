package cn.piflow.bundle.ml_classification

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.ml.classification.DecisionTreeClassifier
import org.apache.spark.sql.SparkSession

class DecisionTreeTraining extends ConfigurableStop{
  val authorEmail: String = "06whuxx@163.com"
  val description: String = "Train a decision tree model"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)
  var training_data_path:String =_
  var model_save_path:String=_
  var maxBins:String=_
  var maxDepth:String=_
  var minInfoGain:String=_
  var minInstancesPerNode:String=_
  var impurity:String=_

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

    //training a Decision Tree model
    val model=new DecisionTreeClassifier()
      .setMaxBins(maxBinsValue)
      .setMaxDepth(maxDepthValue)
      .setMinInfoGain(minInfoGainValue)
      .setMinInstancesPerNode(minInstancesPerNodeValue)
      .setImpurity(impurityValue)
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

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val training_data_path = new PropertyDescriptor().name("training_data_path").displayName("TRAINING_DATA_PATH").defaultValue("").required(true)
    val model_save_path = new PropertyDescriptor().name("model_save_path").displayName("MODEL_SAVE_PATH").description("ddd").defaultValue("").required(true)
    val maxBins=new PropertyDescriptor().name("maxBins").displayName("MAX_BINS").description("Maximum number of bins used for discretizing continuous features and for choosing how to split on features at each node.").defaultValue("").required(true)
    val maxDepth=new PropertyDescriptor().name("maxDepth").displayName("MAX_DEPTH").description("Maximum depth of the tree").defaultValue("").required(true)
    val minInfoGain=new PropertyDescriptor().name("minInfoGain").displayName("MIN_INFO_GAIN").description("Minimum information gain for a split to be considered at a tree node").defaultValue("").required(true)
    val minInstancesPerNode=new PropertyDescriptor().name("minInstancesPerNode").displayName("MIN_INSTANCES_PER_NODE").description("Minimum number of instances each child must have after split.").defaultValue("").required(true)
    val impurity=new PropertyDescriptor().name("impurity").displayName("IMPURITY").description("Criterion used for information gain calculation (case-insensitive). Supported: \"entropy\" and \"gini\". (default = gini)").defaultValue("").required(true)
    descriptor = training_data_path :: descriptor
    descriptor = model_save_path :: descriptor
    descriptor = maxBins :: descriptor
    descriptor = maxDepth :: descriptor
    descriptor = minInfoGain :: descriptor
    descriptor = minInstancesPerNode :: descriptor
    descriptor = impurity :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/ml_classification/DecisionTreeTraining.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.MLGroup.toString)
  }

}
