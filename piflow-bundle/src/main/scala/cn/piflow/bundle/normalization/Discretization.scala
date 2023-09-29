package cn.piflow.bundle.normalization

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.ml.clustering.{KMeans, KMeansModel}
import org.apache.spark.ml.feature.VectorAssembler
import org.apache.spark.ml.feature.Bucketizer
import org.apache.spark.sql.{DataFrame, SparkSession}
import org.apache.spark.ml.feature.QuantileDiscretizer


class Discretization extends ConfigurableStop {

  val authorEmail: String = "zljxnu@163.com"
  val description: String = "continuous numerical discretization"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var inputCol: String = _
  var outputCol: String = _
  var method: String = _
  var numBins: Int = _
  var k: Int = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val df = in.read()

    // 根据用户选择的方法进行相应的离散化
    val discretizedDF = method match {
      case "EqualWidth" => equalWidthDiscretization(df, inputCol, outputCol, numBins)
      case "EqualFrequency" => equalFrequencyDiscretization(df, inputCol, outputCol, numBins)
      case "KMeans" => kMeansDiscretization(df, inputCol, outputCol, k)
      case _ => df // 默认情况下不进行任何处理
    }

    out.write(discretizedDF)
  }

  // 等宽法离散化
  def equalWidthDiscretization(df: DataFrame, inputCol: String, outputCol: String, numBins: Int): DataFrame = {
    val bucketizer = new Bucketizer()
      .setInputCol(inputCol)
      .setOutputCol(outputCol)
//      .setSplits((0 to numBins).map(_.toDouble))
      .setSplits((0 to numBins).map(_.toDouble).toArray)
    bucketizer.transform(df)
  }

//  // 等频离散化
//  def equalFrequencyDiscretization(df: DataFrame, inputCol: String, outputCol: String, numBins: Int): DataFrame = {
//    val discretizer = new QuantileDiscretizer()
//      .setInputCol(inputCol)
//      .setOutputCol(outputCol)
//      .setNumBins(numBins)
//    discretizer.fit(df).transform(df)
//  }
//
//  // 定义一个方法来执行等频离散化
//  def equalFrequencyDiscretization(df: DataFrame, inputCol: String, outputCol: String, numBins: Int ): DataFrame = {
//    // 使用QuantileDiscretizer进行等频离散化
//    val discretizer = new QuantileDiscretizer()
//      .setInputCol(inputCol)
//      .setOutputCol(outputCol)
//      .setNumBins(numBins)
//
//    val dfNew = discretizer.fit(df).transform(df)
//    dfNew
//  }

  // 等频离散化
  def equalFrequencyDiscretization(df: DataFrame, inputCol: String, outputCol: String, numBins: Int): DataFrame = {
    // 创建一个QuantileDiscretizer实例，用于等频离散化
    val discretizer = new QuantileDiscretizer()
      .setInputCol(inputCol) // 设置输入列
      .setOutputCol(outputCol) // 设置输出列
      .setNumBuckets(numBins) // 设置桶的数量

    // 使用数据来拟合(discretizer.fit)并进行离散化转换(discretizer.transform)
    val dfNew = discretizer.fit(df).transform(df)
    dfNew // 返回离散化后的DataFrame
  }

  // 聚类离散化
  def kMeansDiscretization(df: DataFrame, inputCol: String, outputCol: String, k: Int): DataFrame = {
    // 使用KMeans算法将数值列映射到[0, k-1]的整数
    val assembler = new VectorAssembler()
      .setInputCols(Array(inputCol))
      .setOutputCol("features")
    val vectorizedDF = assembler.transform(df)

    val kmeans = new KMeans()
      .setK(k)
      .setSeed(1L)
      .setFeaturesCol("features")
      .setPredictionCol(outputCol)
    val model = kmeans.fit(vectorizedDF)

    val clusteredDF = model.transform(vectorizedDF)
    clusteredDF.drop("features")
  }

  def initialize(ctx: ProcessContext): Unit = {}

  def setProperties(map: Map[String, Any]): Unit = {
    inputCol = MapUtil.get(map, "inputCol").asInstanceOf[String]
    outputCol = MapUtil.get(map, "outputCol").asInstanceOf[String]
    method = MapUtil.get(map, "method").asInstanceOf[String]
    numBins = MapUtil.get(map, "numBins").asInstanceOf[String].toInt
    k = MapUtil.get(map, "k").asInstanceOf[String].toInt
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor: List[PropertyDescriptor] = List()

    val inputColDescriptor = new PropertyDescriptor()
      .name("inputCol")
      .displayName("Input Column")
      .description("The name of the input column to be discretized.")
      .defaultValue("")
      .required(true)

    val outputColDescriptor = new PropertyDescriptor()
      .name("outputCol")
      .displayName("Output Column")
      .description("The name of the output column to store discretized values.")
      .defaultValue("")
      .required(true)

    val methodDescriptor = new PropertyDescriptor()
      .name("method")
      .displayName("Discretization Method")
      .description("Choose the discretization method: EqualWidth, EqualFrequency, or KMeans.")
      .allowableValues(Set("EqualWidth", "EqualFrequency", "KMeans"))
      .defaultValue("EqualWidth")
      .required(true)

    val numBinsDescriptor = new PropertyDescriptor()
      .name("numBins")
      .displayName("Number of Bins")
      .description("The number of bins to use for EqualWidth and EqualFrequency methods.")
      .defaultValue("10")
      .required(false)

    val kDescriptor = new PropertyDescriptor()
      .name("k")
      .displayName("Number of Clusters (KMeans only)")
      .description("The number of clusters to use for the KMeans method.")
      .defaultValue("3")
      .required(false)

    descriptor = inputColDescriptor :: descriptor
    descriptor = outputColDescriptor :: descriptor
    descriptor = methodDescriptor :: descriptor
    descriptor = numBinsDescriptor :: descriptor
    descriptor = kDescriptor :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    // 返回组件图标
    ImageUtil.getImage("icon/normalization/DiscretizationNormalization.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.NormalizationGroup)
  }
}
