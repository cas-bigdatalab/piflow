package cn.piflow.bundle.csv

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf._
import org.apache.spark.sql.SaveMode
import org.apache.spark.sql.execution.arrow.ArrowConverters
import org.apache.spark.sql.{Row, SparkSession}
import org.apache.spark.sql.types.{DataType, StructType}
import org.apache.spark.sql.util.ArrowUtils
import org.apache.arrow.memory.RootAllocator
import org.apache.arrow.vector.ipc.{ArrowFileWriter, WriteChannel}
import org.apache.arrow.vector.{BigIntVector, BitVector, DateDayVector, Float8Vector, IntVector, ValueVector, VarCharVector, VectorSchemaRoot}
import org.apache.arrow.vector.util.VectorBatchAppender

import java.io.{File, FileOutputStream}
import java.net.{ServerSocket, Socket}
import java.nio.channels.Channels
import scala.collection.JavaConverters._
import org.apache.arrow.vector.types.pojo.{ArrowType, Field, FieldType, Schema}
import org.apache.arrow.vector.types.{FloatingPointPrecision, TimeUnit}
import org.apache.spark.sql.types._

import java.nio.charset.StandardCharsets

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf._
import org.apache.arrow.vector.types.pojo.{ArrowType, Field, FieldType, Schema}
import org.apache.arrow.vector.types.{FloatingPointPrecision, TimeUnit}
import org.apache.arrow.vector.{BigIntVector, BitVector, DateDayVector, Float8Vector, IntVector, ValueVector, VarCharVector}
import org.apache.spark.sql.SaveMode
import org.apache.spark.sql.types.{BinaryType, BooleanType, DataType, DateType, DoubleType, FloatType, IntegerType, LongType, StringType, StructType, TimestampType}

import java.nio.charset.StandardCharsets

class CsvSave extends ConfigurableStop{
  val authorEmail: String = "xjzhu@cnic.cn"
  val description: String = "Save the data as a csv file."
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var csvSavePath: String = _
  var header: Boolean = _
  var delimiter: String = _
  var partition :String= _
  var saveMode:String = _

  override def setProperties(map: Map[String, Any]): Unit = {

    csvSavePath = MapUtil.get(map,"csvSavePath").asInstanceOf[String]
    header = MapUtil.get(map,"header").asInstanceOf[String].toBoolean
    delimiter = MapUtil.get(map,"delimiter").asInstanceOf[String]
    partition = MapUtil.get(map,key="partition").asInstanceOf[String]
    saveMode = MapUtil.get(map,"saveMode").asInstanceOf[String]

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {

    val saveModeOption = Set("append","overwrite","error","ignore")
    var descriptor : List[PropertyDescriptor] = List()

    val csvSavePath = new PropertyDescriptor()
      .name("csvSavePath")
      .displayName("CsvSavePath")
      .description("The save path of csv file")
      .defaultValue("")
      .required(true)
      .example("hdfs://127.0.0.1:9000/test/")
    descriptor = csvSavePath :: descriptor

    val header = new PropertyDescriptor()
      .name("header")
      .displayName("Header")
      .description("Whether the csv file has a header")
      .allowableValues(Set("true","false"))
      .defaultValue("false")
      .required(true)
      .example("false")
    descriptor = header :: descriptor

    val delimiter = new PropertyDescriptor()
      .name("delimiter")
      .displayName("Delimiter")
      .description("The delimiter of csv file")
      .defaultValue(",")
      .required(true)
      .example(",")
    descriptor = delimiter :: descriptor

    val partition = new PropertyDescriptor()
      .name("partition")
      .displayName("Partition")
      .description("The partition of csv file,you can specify the number of partitions saved as csv or not")
      .defaultValue("")
      .required(false)
      .example("3")
    descriptor = partition :: descriptor

    val saveMode = new PropertyDescriptor()
      .name("saveMode")
      .displayName("SaveMode")
      .description("The save mode for csv file")
      .allowableValues(saveModeOption)
      .defaultValue("append")
      .required(true)
      .example("append")
    descriptor = saveMode :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/csv/CsvSave.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.CsvGroup)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }
  def sparkTypeToArrowType(dataType: DataType): ArrowType = dataType match {
    case IntegerType    => new ArrowType.Int(32, true)
    case LongType       => new ArrowType.Int(64, true)
    case FloatType      => new ArrowType.FloatingPoint(FloatingPointPrecision.SINGLE)
    case DoubleType     => new ArrowType.FloatingPoint(FloatingPointPrecision.DOUBLE)
    case StringType     => new ArrowType.Utf8()
    case BooleanType    => ArrowType.Bool.INSTANCE
    case BinaryType     => ArrowType.Binary.INSTANCE
    case TimestampType  => new ArrowType.Timestamp(TimeUnit.MILLISECOND, null)
    case _              => throw new UnsupportedOperationException(s"Unsupported type: $dataType")
  }

  def toArrowSchema(schema: StructType): Schema = {
    val fields = schema.fields.map { field =>
      new Field(
        field.name,
        FieldType.nullable(sparkTypeToArrowType(field.dataType)),
        null
      )
    }.toList
    new Schema(fields.asJava)
  }

  type FieldProcessor = (Int, Any) => Unit
  private def createFieldProcessor(sparkType: DataType, vector: ValueVector): FieldProcessor =
    (sparkType, vector) match {
      // Int 类型 (Integer/Numeric)
      case (_: IntegerType, vec: IntVector) => (rowIdx, value) =>
        if (value == null) vec.setNull(rowIdx)
        else vec.setSafe(rowIdx, value.asInstanceOf[Int])
      // 字符串类型
      case (_: StringType, vec: VarCharVector) => (rowIdx, value) =>
        if (value == null) {
          vec.setNull(rowIdx)
        } else {
          val strValue = value.toString
          val bytes = strValue.getBytes(StandardCharsets.UTF_8)
          vec.setSafe(rowIdx, bytes, 0, bytes.length)
        }
      // Double 类型
      case (_: DoubleType, vec: Float8Vector) => (rowIdx, value) =>
        if (value == null) vec.setNull(rowIdx)
        else vec.setSafe(rowIdx, value.asInstanceOf[Double])
      // Long 类型
      case (_: LongType, vec: BigIntVector) => (rowIdx, value) =>
        if (value == null) vec.setNull(rowIdx)
        else vec.setSafe(rowIdx, value.asInstanceOf[Long])
      // Boolean 类型（使用 BitVector）
      case (_: BooleanType, vec: BitVector) => (rowIdx, value) =>
        if (value == null) vec.setNull(rowIdx)
        else vec.setSafe(rowIdx, if (value.asInstanceOf[Boolean]) 1 else 0)
      // Date类型（示例）
      case (_: DateType, vec: DateDayVector) => (rowIdx, value) =>
        if (value == null) vec.setNull(rowIdx)
        else vec.setSafe(rowIdx, value.asInstanceOf[Int]) // 需根据实际日期格式转换
      case _ => throw new IllegalArgumentException(
        s"Unsupported type combination: SparkType=$sparkType, VectorType=${vector.getClass}"
      )
    }

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val df = in.read().getSparkDf

        val allocator = new RootAllocator(Long.MaxValue)
        val arrowSchema = toArrowSchema(df.schema)
        val root = VectorSchemaRoot.create(arrowSchema, allocator)

        val serverSocket = new ServerSocket(9090)

        println("Server is listening on port 9090")


        try {
          root.allocateNew()
          // 创建类型映射的字段处理器
          val fieldProcessors = df.schema.zipWithIndex.map { case (field, idx) =>
            createFieldProcessor(field.dataType, root.getVector(idx)) // 动态绑定对应 Vector 类型
          }
          // 逐行处理数据
          val rows = df.collect().toList
          root.setRowCount(rows.size)
          for {
            (row, rowIndex) <- rows.zipWithIndex
            (value, processor) <- row.toSeq.zip(fieldProcessors)
          } {
            processor(rowIndex, value) // 类型安全地写入数据
          }
          val socket: Socket = serverSocket.accept()
          val writer = new ArrowFileWriter(root, null, Channels.newChannel(socket.getOutputStream))
          try {

            writer.start()
            writer.writeBatch()
            writer.end()
          } finally {
            writer.close()
            socket.close()
          }
        } finally {
          root.close()
          allocator.close()
        }


    if("".equals(partition)){
      df.write
        .format("csv")
        .mode(saveMode)
        .option("header", header)
        .option("delimiter",delimiter)
        .save(csvSavePath)
    }else{
      df.repartition(partition.toInt).write
        .format("csv")
        .mode(saveMode)
        .option("header", header)
        .option("delimiter",delimiter)
        .save(csvSavePath)
    }
  }
}

