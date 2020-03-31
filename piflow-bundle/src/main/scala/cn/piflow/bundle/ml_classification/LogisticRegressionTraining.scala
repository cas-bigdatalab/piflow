package cn.piflow.bundle.ml_classification

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.SparkSession
import org.apache.spark.ml.classification.LogisticRegression

class LogisticRegressionTraining extends ConfigurableStop{
  val authorEmail: String = "06whuxx@163.com"
  val description: String = "Train a logistic regression model"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)
  var training_data_path:String =_
  var model_save_path:String=_
  var maxIter:String=_
  var minTol:String=_
  var regParam:String=_
  var elasticNetParam:String=_
  var threshold:String=_
  var family:String=_

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()

    //load data stored in libsvm format as a dataframe
    val data=spark.read.format("libsvm").load(training_data_path)

    //Param for maximum number of iterations (>= 0)
    var maxIterValue:Int=50
    if(maxIter!=""){
      maxIterValue=maxIter.toInt
    }

    //Param for the convergence tolerance for iterative algorithms (>= 0)
    var minTolValue:Double=1E-6
    if(minTol!=""){
      minTolValue=minTol.toDouble
    }

    //Param for regularization parameter (>= 0).
    var regParamValue:Double=0.2
    if(regParam!=""){
      regParamValue=regParam.toDouble
    }

    //Param for the ElasticNet mixing parameter, in range [0, 1].
    var elasticNetParamValue:Double=0
    if(elasticNetParam!=""){
      elasticNetParamValue=elasticNetParam.toDouble
    }

    //Param for threshold in binary classification prediction, in range [0, 1]
    var thresholdValue:Double=0.5
    if(threshold!=""){
      thresholdValue=threshold.toDouble
    }

    //Param for the name of family which is a description of the label distribution to be used in the model
    var familyValue="auto"
    if(family!=""){
      familyValue=family
    }

    //training a Logistic Regression model
    val model=new LogisticRegression()
      .setMaxIter(maxIterValue)
      .setTol(minTolValue)
      .setElasticNetParam(regParamValue)
      .setElasticNetParam(elasticNetParamValue)
      .setThreshold(thresholdValue)
      .setFamily(familyValue)
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
    regParam=MapUtil.get(map,key="regParam").asInstanceOf[String]
    elasticNetParam=MapUtil.get(map,key="elasticNetParam").asInstanceOf[String]
    threshold=MapUtil.get(map,key="threshold").asInstanceOf[String]
    family=MapUtil.get(map,key="family").asInstanceOf[String]

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val training_data_path = new PropertyDescriptor().name("training_data_path").displayName("TRAINING_DATA_PATH").defaultValue("").required(true)
    val model_save_path = new PropertyDescriptor().name("model_save_path").displayName("MODEL_SAVE_PATH").description("ddd").defaultValue("").required(true)
    val maxIter=new PropertyDescriptor().name("maxIter").displayName("MAX_ITER").description("Param for maximum number of iterations").defaultValue("").required(false)
    val minTol=new PropertyDescriptor().name("minTol").displayName("MIN_TOL").description("Param for the convergence tolerance for iterative algorithms (>= 0)").defaultValue("").required(false)
    val regParam=new PropertyDescriptor().name("regParam").displayName("REG_PARAM").description("Param for regularization parameter (>= 0)").defaultValue("").required(false)
    val elasticNetParam=new PropertyDescriptor().name("elasticNetParam").displayName("ELASTIC_NET_PARAM").description("Param for the ElasticNet mixing parameter, in range [0, 1]").defaultValue("").required(false)
    val threshold=new PropertyDescriptor().name("threshold").displayName("THRESHOLD").description("Param for threshold in binary classification prediction, in range [0, 1]").defaultValue("").required(false)
    val family=new PropertyDescriptor().name("family").displayName("FAMILY").description("Param for the name of family which is a description of the label distribution to be used in the model").defaultValue("").required(false)
    descriptor = training_data_path :: descriptor
    descriptor = model_save_path :: descriptor
    descriptor = maxIter :: descriptor
    descriptor = minTol :: descriptor
    descriptor = regParam :: descriptor
    descriptor = elasticNetParam :: descriptor
    descriptor = threshold :: descriptor
    descriptor = family :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/ml_classification/LogisticRegressionTraining.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.MLGroup.toString)
  }


}
