package cn.piflow.bundle.normalization

import cn.piflow._
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.sql.{DataFrame, SparkSession}

class MaxMinNormalization extends ConfigurableStop {
  // 作者信息
  val authorEmail: String = "zljxnu@163.com"
  // 组件描述
  val description: String = "maximum and minimum value standardization"
  // 输入端口列表
  val inportList: List[String] = List(Port.DefaultPort)
  // 输出端口列表
  val outportList: List[String] = List(Port.DefaultPort)

  // 定义属性：要标准化的列名
  var inputCol: String = _

  // 定义属性：输出列名
  var outputCol: String = _

  // 初始化方法
  def initialize(ctx: ProcessContext): Unit = {}

  // 执行方法
  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    // 获取 SparkSession
    val spark = pec.get[SparkSession]()

    // 从输入端口读取数据
    val df = in.read()

    // 计算列的最大值和最小值
    val max = df.agg(Map(inputCol -> "max")).collect()(0)(0).asInstanceOf[Double]
    val min = df.agg(Map(inputCol -> "min")).collect()(0)(0).asInstanceOf[Double]

    // 使用公式进行最小-最大值标准化
    val scaledDf: DataFrame = df.withColumn(outputCol, (df(inputCol) - min) / (max - min))

    // 将标准化后的数据写入输出端口
    out.write(scaledDf)
  }

  // 设置属性
  def setProperties(map: Map[String, Any]): Unit = {
    inputCol = MapUtil.get(map, "inputCol").asInstanceOf[String]
    outputCol = MapUtil.get(map, "outputCol").asInstanceOf[String]
  }

  // 获取属性描述
  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor: List[PropertyDescriptor] = List()
    val inputCol = new PropertyDescriptor()
      .name("inputCol")
      .displayName("输入列名")
      .description("要进行最小-最大值标准化的列名")
      .defaultValue("")
      .required(true)

    val outputCol = new PropertyDescriptor()
      .name("outputCol")
      .displayName("Column_Name输出列名")
      .description("Column names with numerical data to be scaled 标准化后的列名")
      .defaultValue("")
      .required(true)

    descriptor = inputCol :: outputCol :: descriptor
    descriptor
  }

  // 获取组件图标
  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/normalization/MaxMinNormalization.png")
  }

  // 获取组件所属的组
  override def getGroup(): List[String] = {
    List(StopGroup.NormalizationGroup)
  }
}


//package cn.piflow.bundle.normalization
//
//import cn.piflow.bundle.util.CleanUtil
//import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
//import cn.piflow.conf._
//import cn.piflow.conf.bean.PropertyDescriptor
//import cn.piflow.conf.util.{ImageUtil, MapUtil}
//import org.apache.spark.sql.SparkSession
//
//class MaxMinNormalization extends ConfigurableStop {
//
//  // 作者邮箱
//  val authorEmail: String = "zljxnu@163.com"
//  // 描述
//  val description: String = "MinMax scaling for numerical data"
//  // 输入端口列表
//  val inportList: List[String] = List(Port.DefaultPort)
//  // 输出端口列表
//  val outportList: List[String] = List(Port.DefaultPort)
//
//  // 需要标准化的列名，从属性中设置
//  var columnName: String = _
//
//  // 执行标准化操作
//  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
//    val spark = pec.get[SparkSession]()
//    val sqlContext = spark.sqlContext
//    // 读取输入数据
//    val dfOld = in.read()
//    // 将输入数据创建为临时表
//    dfOld.createOrReplaceTempView("data")
//    // 解析需要标准化的列名
//    val columnNames = columnName.split(",").toSet
//
//    val sqlNewFieldStr = new StringBuilder
//    // 针对每个指定的列名，生成标准化的 SQL 代码
//    columnNames.foreach(c => {
//      sqlNewFieldStr ++= ",((("
//      sqlNewFieldStr ++= c
//      sqlNewFieldStr ++= " - min("
//      sqlNewFieldStr ++= c
//      sqlNewFieldStr ++= ")) / (max("
//      sqlNewFieldStr ++= c
//      sqlNewFieldStr ++= ") - min("
//      sqlNewFieldStr ++= c
//      sqlNewFieldStr ++= "))) as "
//      sqlNewFieldStr ++= c
//      sqlNewFieldStr ++= "_scaled "
//    })
//
//    // 构建最终的 SQL 查询文本
//    val sqlText: String = "select * " + sqlNewFieldStr + " from data"
//
//    // 执行 SQL 查询，得到标准化后的 DataFrame
//    val dfNew = sqlContext.sql(sqlText)
//    dfNew.createOrReplaceTempView("scaled_data")
//
//    // 将标准化后的数据写入输出
//    out.write(dfNew)
//  }
//
//  // 初始化方法
//  def initialize(ctx: ProcessContext): Unit = {}
//
//  // 设置属性
//  def setProperties(map: Map[String, Any]): Unit = {
//    // 从属性映射中获取需要标准化的列名
//    columnName = MapUtil.get(map, key = "columnName").asInstanceOf[String]
//  }
//
//  // 定义属性描述符
//  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
//    var descriptor: List[PropertyDescriptor] = List()
//    val columnNameDesc = new PropertyDescriptor()
//      .name("columnName")
//      .displayName("Column_Name")
//      .description("Column names with numerical data to be scaled (comma-separated)")
//      .defaultValue("")
//      .required(true)
//      .example("feature1,feature2")
//
//    descriptor = columnNameDesc :: descriptor
//    descriptor
//  }
//
//  // 获取图标
//  override def getIcon(): Array[Byte] = {
//    ImageUtil.getImage("icon/normalization/MaxMinNormalization.png")
//  }
//
//  // 获取所属组
//  override def getGroup(): List[String] = {
//    List(StopGroup.NormalizationGroup)
//  }
//}
