package cn.piflow.bundle.ml_classification

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroupEnum}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.MapUtil
import org.apache.spark.ml.classification.RandomForestClassificationModel
import org.apache.spark.sql.SparkSession

class RandomForestPrediction extends ConfigurableStop{
  val authorEmail: String = "xiaoxiao@cnic.cn"
  val description: String = "Make use of a exist RandomForest Model to predict."
  val inportList: List[String] = List(PortEnum.NonePort.toString)
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)
  var test_data_path:String =_
  var model_path:String=_


  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    //load data stored in libsvm format as a dataframe
    val data=spark.read.format("libsvm").load(test_data_path)
    //data.show()

    //load model
    val model=RandomForestClassificationModel.load(model_path)

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

  override def getIcon(): Array[Byte] = ???

  override def getGroup(): List[String] = {
    List(StopGroupEnum.MLGroup.toString)
  }

}
