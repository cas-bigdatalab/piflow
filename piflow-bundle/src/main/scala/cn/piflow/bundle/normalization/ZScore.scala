package cn.piflow.bundle.normalization

import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.{DataFrame, SparkSession}
import org.apache.spark.sql.functions._

class ZScore extends ConfigurableStop {

  // 作者邮箱
  val authorEmail: String = "zljxnu@163.cn"
  // 描述
  val description: String = "ZScore standardization"
  // 输入端口
  val inportList: List[String] = List(Port.DefaultPort)
  // 输出端口
  val outportList: List[String] = List(Port.DefaultPort)

  // 输入列名称
  var inputCols: String = _
  // 输出列名称
  var outputCols: String = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val df = in.read()

    // 将逗号分隔的输入和输出列名称拆分为列表
    val inputColList = inputCols.split(",").map(_.trim)
    val outputColList = outputCols.split(",").map(_.trim)

    // 计算均值和标准差
    val stats = inputColList.foldLeft(df) {
      case (currentDf, inputCol) =>
        val mean = currentDf.select(avg(col(inputCol))).first().getDouble(0)
        val stdDev = currentDf.select(stddev(col(inputCol))).first().getDouble(0)
        // 创建一个新列名：{inputCol}_zscore
        val zScoreCol = s"${inputCol}_zscore"

        // 使用公式进行 z-score 标准化
        currentDf.withColumn(zScoreCol, (col(inputCol) - mean) / stdDev)
    }

    // 重命名输出列以匹配原始列名称
    val finalDf = inputColList.zip(outputColList).foldLeft(stats) {
      case (currentDf, (inputCol, outputCol)) =>
        currentDf.withColumnRenamed(s"${inputCol}_zscore", outputCol)
    }

    out.write(finalDf)
  }

  def initialize(ctx: ProcessContext): Unit = {}

  def setProperties(map: Map[String, Any]): Unit = {
    inputCols = MapUtil.get(map, key = "inputCols").asInstanceOf[String]
    outputCols = MapUtil.get(map, key = "outputCols").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor: List[PropertyDescriptor] = List()
    val inputCols = new PropertyDescriptor()
      .name("inputCols")
      .displayName("输入列")
      .description("要标准化的列，用逗号分隔。")
      .defaultValue("")
      .required(true)
      .example("特征1, 特征2")

    val outputCols = new PropertyDescriptor()
      .name("outputCols")
      .displayName("输出列")
      .description("用于存储标准化值的相应输出列，用逗号分隔。")
      .defaultValue("")
      .required(true)
      .example("标准化特征1, 标准化特征2")

    descriptor = inputCols :: outputCols :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/normalization/ZScoreNormalization.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.NormalizationGroup)
  }
}
