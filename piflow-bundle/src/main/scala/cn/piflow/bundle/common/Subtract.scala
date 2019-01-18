package cn.piflow.bundle.common

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.ImageUtil
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.api.java.JavaRDD
import org.apache.spark.sql.types.StructType
import org.apache.spark.sql.{DataFrame, Row, SparkSession}

class Subtract extends ConfigurableStop{
  override val authorEmail: String = "yangqidong@cnic.cn"
  override val description: String = "Delete duplicates of the first and second tables from the first table"
  override val inportList: List[String] =List(PortEnum.AnyPort.toString)
  override val outportList: List[String] = List(PortEnum.DefaultPort.toString)

  override def setProperties(map: Map[String, Any]): Unit = {
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("common/subtract.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.CommonGroup.toString)
  }


  override def initialize(ctx: ProcessContext): Unit = {

  }

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()

    val dfs: Seq[DataFrame] = in.ports().map(in.read(_))
    var df1: DataFrame = dfs(0)
    var df2: DataFrame = dfs(1)

    val rdd: JavaRDD[Row] = df1.toJavaRDD.subtract(df2.toJavaRDD)

    val schema: StructType = df1.schema
    val outDF: DataFrame = spark.createDataFrame(rdd,schema)

    out.write(outDF)
  }
}
