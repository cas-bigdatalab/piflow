package cn.piflow.bundle.common

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.ImageUtil
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.util.PropertyUtil
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.SparkSession

import java.io.File
import java.util.UUID

class CheckPoint extends ConfigurableStop{
  override val authorEmail: String = "ygang@cnic.cn"
  override val description: String = "检查点机制"
  override val inportList: List[String] = List(Port.DefaultPort)
  override val outportList: List[String] = List(Port.DefaultPort)

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    //    获取数据缓存路径
    var checkPoint_path = PropertyUtil.getPropertyValue("checkpoint.path")
    if(checkPoint_path.endsWith(File.separator)) {
      checkPoint_path = checkPoint_path + UUID.randomUUID()
    }else{
      checkPoint_path = checkPoint_path + File.separator + UUID.randomUUID()
    }
    println("临时数据缓存路径："+checkPoint_path)

    val spark = pec.get[SparkSession]()
    val df_checkPoint = in.read()

//    df_checkPoint.write.format("csv").mode("overwrite").option("header", true).save(checkPoint_path)
//    Thread.sleep(5*1000)
//    val outDf_checkPoint = spark.read.option("header", true).option("inferSchema", true).csv(checkPoint_path)

    df_checkPoint.write.parquet(checkPoint_path)
    Thread.sleep(5*1000)
    val outDf_checkPoint = spark.read.parquet(checkPoint_path)

    out.write(outDf_checkPoint)
  }
  override def setProperties(map: Map[String, Any]): Unit = {

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    descriptor
  }


  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/csv/CsvParser.png",this.getClass.getName)
  }

  override def getGroup(): List[String] = {
    List(StopGroup.CommonGroup)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }
}
