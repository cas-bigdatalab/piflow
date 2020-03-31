package cn.piflow.bundle.ml_classification

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.ml.classification.MultilayerPerceptronClassifier
import org.apache.spark.sql.SparkSession

class MultilayerPerceptronTraining extends ConfigurableStop{
  val authorEmail: String = "xiaoxiao@cnic.cn"
  val description: String = "Train a multilayer perceptron model"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)
  var training_data_path:String =_
  var model_save_path:String=_
  var layers:String=_
  var maxIter:String=_
  var stepSize:String=_
  var thresholds:String=_
  var minTol:String=_


  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()

    //load data stored in libsvm format as a dataframe
    val data=spark.read.format("libsvm").load(training_data_path)

    //Layer sizes including input size and output size.
    var layersValue:Array[Int]=Array()
    if(layers==""){
      throw new IllegalArgumentException
    }else{
       layersValue=layers.substring(1,layers.length-1).split(",").map(_.toInt)
    }

    //Param for Thresholds in multi-class classification to adjust the probability of predicting each class.Sample format:(0.6,0.4)
    var thresholdsValue:Array[Double]=Array()
    if(thresholds==""){
      throw new IllegalArgumentException
    }else{
      thresholdsValue=thresholds.substring(1,layers.length-1).split(",").map(_.toDouble)
    }


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

    //Param for Step size to be used for each iteration of optimization (> 0).
    var stepSizeValue:Double=0.8
    if(stepSize!=""){
      stepSizeValue=stepSize.toDouble
    }

    //training a MultilayerPerceptron model
    val model=new MultilayerPerceptronClassifier()
      .setMaxIter(maxIterValue)
      .setTol(minTolValue)
      .setStepSize(stepSizeValue)
      .setLayers(layersValue)
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
    thresholds=MapUtil.get(map,key="thresholds").asInstanceOf[String]
    stepSize=MapUtil.get(map,key="stepSize").asInstanceOf[String]
    layers=MapUtil.get(map,key="layers").asInstanceOf[String]

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val training_data_path = new PropertyDescriptor().name("training_data_path").displayName("TRAINING_DATA_PATH").defaultValue("").required(true)
    val model_save_path = new PropertyDescriptor().name("model_save_path").displayName("MODEL_SAVE_PATH").description("").defaultValue("").required(true)
    val maxIter=new PropertyDescriptor().name("maxIter").displayName("MAX_ITER").description("Param for maximum number of iterations (>= 0).").defaultValue("").required(false)
    val minTol=new PropertyDescriptor().name("minTol").displayName("MIN_TOL").description("Param for the convergence tolerance for iterative algorithms (>= 0).").defaultValue("").required(false)
    val stepSize=new PropertyDescriptor().name("stepSize").displayName("STEP_SIZE").description("Param for Step size to be used for each iteration of optimization (> 0).").defaultValue("").required(false)
    val thresholds=new PropertyDescriptor().name("thresholds").displayName("THRESHOLDS").description("DoubleArrayParam.Param for Thresholds in multi-class classification to adjust the probability of predicting each class. Array must have length equal to the number of classes, with values > 0 excepting that at most one value may be 0. The class with largest value p/t is predicted, where p is the original probability of that class and t is the class's threshold.").defaultValue("").required(true)
    val layers=new PropertyDescriptor().name("layers").displayName("LAYERS").description("Layer sizes including input size and output size. ").defaultValue("").required(true)
    descriptor = training_data_path :: descriptor
    descriptor = model_save_path :: descriptor
    descriptor = maxIter :: descriptor
    descriptor = minTol :: descriptor
    descriptor = stepSize :: descriptor
    descriptor = thresholds :: descriptor
    descriptor = layers :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/ml_classification/MultilayerPerceptronTraining.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.MLGroup.toString)
  }

}
