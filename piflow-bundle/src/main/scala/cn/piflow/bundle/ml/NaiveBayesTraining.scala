package cn.piflow.bundle.ml

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.bundle.util.{JedisClusterImplSer, RedisUtil}
import cn.piflow.conf.{ConfigurableStop, StopGroupEnum}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.MapUtil
import org.apache.spark.ml.classification.NaiveBayes
import org.apache.spark.sql.SparkSession

class NaiveBayesTraining extends ConfigurableStop{
  val inportCount: Int = 1
  val outportCount: Int = 0
  var training_data_path:String =_

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()

    //load data stored in libsvm format as a dataframe
    val data=spark.read.format("libsvm").load("/root/watermellonDataset.txt")

    //training a NaiveBayes model
    val model=new NaiveBayes().fit(data)

    val predictions=model.transform(data)
    predictions.show()

  }

  def initialize(ctx: ProcessContext): Unit = {

  }


  def setProperties(map: Map[String, Any]): Unit = {
    training_data_path=MapUtil.get(map,key="training_data_path").asInstanceOf[String]

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val training_data_path = new PropertyDescriptor().name("training_data_path").displayName("TRAINING_DATA_PATH").defaultValue("").required(true)
    descriptor = training_data_path :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = ???

  override def getGroup(): List[String] = {
    List(StopGroupEnum.MLGroup.toString)
  }

  override val authorEmail: String = "xiaoxiao@cnic.cn"

}
