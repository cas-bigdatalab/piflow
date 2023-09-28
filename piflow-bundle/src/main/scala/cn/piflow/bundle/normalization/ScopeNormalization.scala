package cn.piflow.bundle.normalization

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.sql.functions._
import org.apache.spark.sql.{DataFrame, SparkSession}

class ScopeNormalization extends ConfigurableStop {

  // 组件的作者信息
  val authorEmail: String = "zljxnu@163.com"
  // 组件的描述信息
  val description: String = "Scope standardization"
  // 定义输入端口
  val inportList: List[String] = List(Port.DefaultPort)
  // 定义输出端口
  val outportList: List[String] = List(Port.DefaultPort)

  // 定义输入列名称
  var inputCol: String = _
  // 定义输出列名称
  var outputCol: String = _
  // 定义目标范围 [a, b]
  var range: (Double, Double) = (0.0, 1.0)

  // 实际的数据处理逻辑
  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    // 获取SparkSession
    val spark = pec.get[SparkSession]()

    // 读取输入数据
    val dfOld = in.read()

    // 使用范围映射公式进行数据处理
    val dfNew = mapToRange(dfOld, inputCol, outputCol, range)

    // 将处理后的数据写出
    out.write(dfNew)
  }

  // 初始化方法
  def initialize(ctx: ProcessContext): Unit = {}

  // 设置组件属性
  def setProperties(map: Map[String, Any]): Unit = {
    inputCol = MapUtil.get(map, key = "inputCol").asInstanceOf[String]
    outputCol = MapUtil.get(map, key = "outputCol").asInstanceOf[String]
    val values = MapUtil.get(map, key = "range").asInstanceOf[String].stripPrefix("(").stripSuffix(")").split(",").map(_.toDouble)
    range = (values(0), values(1))

////    range = MapUtil.get(map, key = "range").asInstanceOf[(Double, Double)]
//    //把string解析成元组映射给range
//    val jsonString: String = MapUtil.get(map, key = "range").asInstanceOf[String]
//    // 移除括号并分割字符串
//    val values = jsonString.stripPrefix("(").stripSuffix(")").split(",").map(_.toDouble)
//    // 创建 Scala 元组
//    val range: (Double, Double) = (values(0), values(1))



  }

  // 定义组件的属性描述
  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor: List[PropertyDescriptor] = List()
    val inputCol = new PropertyDescriptor()
      .name("inputCol")
      .displayName("Input Column")
      .description("要映射的输入列的名称")
      .defaultValue("")
      .required(true)
      .example("input_data")

    val outputCol = new PropertyDescriptor()
      .name("outputCol")
      .displayName("Output Column")
      .description("映射后的输出列的名称")
      .defaultValue("")
      .required(true)
      .example("normalized_data")

    val range = new PropertyDescriptor()
      .name("range")
      .displayName("Range")
      .description("目标范围 [a, b]，以元组的形式表示")
      .defaultValue("")
      .required(true)
      .example("(0.0, 1.0)")

    descriptor = inputCol :: outputCol :: range :: descriptor
    descriptor
  }

  // 定义组件的图标（可选）
  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/normalization/ScopeNormalization.png")
  }

  // 定义组件所属的分组（可选）
  override def getGroup(): List[String] = {
    List(StopGroup.NormalizationGroup)
  }

  // 实现范围映射的方法
  private def mapToRange(df: DataFrame, inputCol: String, outputCol: String, range: (Double, Double)): DataFrame = {
    // 使用Spark SQL的functions库来进行数据处理
    val min = df.agg(Map(inputCol -> "min")).collect()(0)(0).asInstanceOf[Double]
    val max = df.agg(Map(inputCol -> "max")).collect()(0)(0).asInstanceOf[Double]
    val dfNew = df.withColumn(outputCol, (col(inputCol) - min) / (max - min) * (range._2 - range._1) + range._1)
    dfNew
  }
}