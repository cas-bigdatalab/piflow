package cn.piflow.bundle.ml

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.bundle.util.{JedisClusterImplSer, RedisUtil}
import cn.piflow.conf.{ConfigurableStop, StopGroupEnum}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.MapUtil
//import org.apache.spark.ml.classification.{NaiveBayes, NaiveBayesModel}
import org.apache.spark.sql.SparkSession
import redis.clients.jedis.HostAndPort

class NaiveBayesPrediction extends ConfigurableStop{
  val description: String = "Mllib naive bayes prediction."
  val inportCount: Int = 1
  val outportCount: Int = 0
  var test_data_path:String =_
  var model_path:String=_


  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    //load data stored in libsvm format as a dataframe
    val data=spark.read.format("libsvm").load(test_data_path)
    //data.show()

    //load model
    //val model=NaiveBayesModel.load(model_path)

    //val predictions=model.transform(data)
    //predictions.show()
    //out.write(predictions)

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
    List(/*StopGroupEnum.MLGroup.toString*/"")
  }

  override val authorEmail: String = "xiaoxiao@cnic.cn"

}
