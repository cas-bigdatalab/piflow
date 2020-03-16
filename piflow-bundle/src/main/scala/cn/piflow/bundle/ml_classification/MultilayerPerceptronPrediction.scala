package cn.piflow.bundle.ml_classification

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.ml.classification.MultilayerPerceptronClassificationModel
import org.apache.spark.sql.SparkSession

class MultilayerPerceptronPrediction extends ConfigurableStop{
  val authorEmail: String = "06whuxx@163.com"
  val description: String = "Use an existing multilayer perceptron model to predict"
  val inportList: List[String] = List(Port.DefaultPort.toString)
  val outportList: List[String] = List(Port.DefaultPort.toString)
  var test_data_path:String =_
  var model_path:String=_


  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    //load data stored in libsvm format as a dataframe
    val data=spark.read.format("libsvm").load(test_data_path)
    //data.show()

    //load model
    val model=MultilayerPerceptronClassificationModel.load(model_path)

    val predictions=model.transform(data)
    predictions.show()
    out.write(predictions)

  }

  def initialize(ctx: ProcessContext): Unit = {

  }


  def setProperties(map: Map[String, Any]): Unit = {
    test_data_path=MapUtil.get(map,key="test_data_path").asInstanceOf[String]
    model_path=MapUtil.get(map,key="model_path").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val test_data_path = new PropertyDescriptor().name("test_data_path").displayName("TEST_DATA_PATH").defaultValue("").required(true)
    val model_path = new PropertyDescriptor().name("model_path").displayName("MODEL_PATH").defaultValue("").required(true)
    descriptor = test_data_path :: descriptor
    descriptor = model_path :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/ml_classification/MultilayerPerceptronPrediction.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.MLGroup.toString)
  }

}
