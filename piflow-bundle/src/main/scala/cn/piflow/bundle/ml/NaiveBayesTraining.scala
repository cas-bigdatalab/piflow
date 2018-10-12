package cn.piflow.bundle.ml

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.bundle.util.{JedisClusterImplSer, RedisUtil}
import cn.piflow.conf.{ConfigurableStop, StopGroupEnum}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.MapUtil
//import org.apache.spark.ml.classification._

import org.apache.spark.sql.SparkSession

class NaiveBayesTraining extends ConfigurableStop{
  val inportCount: Int = 1
  val outportCount: Int = 0
  var training_data_path:String =_
  var smoothing_value:String=_
  var model_save_path:String=_


  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    /*val spark = pec.get[SparkSession]()

    //load data stored in libsvm format as a dataframe
    val data=spark.read.format("libsvm").load(training_data_path)

    //get smoothing factor
    var smoothing_factor:Double=0
    if(smoothing_value!=""){
      smoothing_factor=smoothing_value.toDouble
    }

    //training a NaiveBayes model
    val model=new NaiveBayes().setSmoothing(smoothing_factor).fit(data)

    //model persistence
    model.save(model_save_path)

    import spark.implicits._
    val dfOut=Seq(model_save_path).toDF
    dfOut.show()
    out.write(dfOut)*/

  }

  def initialize(ctx: ProcessContext): Unit = {

  }


  def setProperties(map: Map[String, Any]): Unit = {
    training_data_path=MapUtil.get(map,key="training_data_path").asInstanceOf[String]
    smoothing_value=MapUtil.get(map,key="smoothing_value").asInstanceOf[String]
    model_save_path=MapUtil.get(map,key="model_save_path").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val training_data_path = new PropertyDescriptor().name("training_data_path").displayName("TRAINING_DATA_PATH").defaultValue("").required(true)
    val smoothing_value = new PropertyDescriptor().name("smoothing_value").displayName("SMOOTHING_FACTOR").defaultValue("0").required(false)
    val model_save_path = new PropertyDescriptor().name("model_save_path").displayName("MODEL_SAVE_PATH").defaultValue("").required(true)
    descriptor = training_data_path :: descriptor
    descriptor = smoothing_value :: descriptor
    descriptor = model_save_path :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = ???

  override def getGroup(): List[String] = {
    List(/*StopGroupEnum.MLGroup.toString*/"")
  }

  override val authorEmail: String = "xiaoxiao@cnic.cn"

}
