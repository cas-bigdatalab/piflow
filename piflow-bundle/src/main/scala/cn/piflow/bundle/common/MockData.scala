package cn.piflow.bundle.common


import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.sql.{DataFrame, SparkSession}
import org.apache.spark.sql.types._
import org.json4s
import org.json4s.JsonAST._
import org.json4s.jackson.JsonMethods._

import scala.util.Random

class MockData extends ConfigurableStop{
  override val authorEmail: String = "xjzhu@cnic.cn"
  override val description: String = "Mock dataframe."
  override val inportList: List[String] = List(Port.DefaultPort)
  override val outportList: List[String] = List(Port.DefaultPort)

  var schema: String = _
  var count: Int = _

  override def setProperties(map: Map[String, Any]): Unit = {
    schema = MapUtil.get(map,"schema").asInstanceOf[String]
    count = MapUtil.get(map,"count").asInstanceOf[String].toInt
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val schema = new PropertyDescriptor()
      .name("schema")
      .displayName("Schema")
      .description("The schema of mock data, format is column:columnType:isNullable. " +
        "Separate multiple fields with commas. " +
        "columnType can be String/Int/Long/Float/Double/Boolean. " +
        "isNullable can be left blank, the default value is false. ")
      .defaultValue("")
      .required(true)
      .example("id:String,name:String,age:Int")
    descriptor = schema :: descriptor

    val count = new PropertyDescriptor()
      .name("count")
      .displayName("Count")
      .description("The count of dataframe")
      .defaultValue("")
      .required(true)
      .example("10")
    descriptor = count :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/common/MockData.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.CommonGroup)
  }

  override def initialize(ctx: ProcessContext): Unit = {}

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    import spark.implicits._

    val field = this.schema.split(",")
    val structFieldArray : Array[StructField] = new Array[StructField](field.size)
    for(i <- 0 to field.size - 1){
      val columnInfo = field(i).trim.split(":")
      val column = columnInfo(0).trim
      val columnType = columnInfo(1).trim
      var isNullable = false
      if(columnInfo.size == 3){
        isNullable = columnInfo(2).trim.toBoolean
      }
      columnType match {
        case "String"=> structFieldArray(i) = new StructField(column, StringType, isNullable)
        case "Int"=>structFieldArray(i) = new StructField(column, IntegerType, isNullable)
        case "Double"=>structFieldArray(i) = new StructField(column, DoubleType, isNullable)
        case "Float"=>structFieldArray(i) = new StructField(column, FloatType, isNullable)
        case "Long"=>structFieldArray(i) = new StructField(column, LongType, isNullable)
        case "Boolean"=>structFieldArray(i) = new StructField(column, BooleanType, isNullable)
        //case "Date"=>structFieldArray(i) = new StructField(column, DateType, nullable = true)
        //case "Timestamp"=>structFieldArray(i) = new StructField(column, TimestampType, nullable = true)
      }
    }
    val schemaStructType = StructType(structFieldArray)
    val rnd : Random = new Random()
    val df = spark.read.schema(schemaStructType).json((0 to count -1 ).map{ _ => compact(randomJson(rnd,schemaStructType))}.toDS())
    out.write(df)
  }

  private def randomJson( rnd: Random, dataType : DataType): JValue ={

    val alpha = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    dataType match {
      case v:DoubleType =>
        json4s.JDouble(rnd.nextDouble())
      case v:StringType =>
        JString((1 to 10).map(x => alpha(Random.nextInt.abs % alpha.size)).mkString)
      case v:IntegerType =>
        JInt(rnd.nextInt(100))
      case v:LongType =>
        JInt(rnd.nextLong())
      case v:FloatType =>
        JDouble(rnd.nextFloat())
      case v:BooleanType =>
        JBool(rnd.nextBoolean())
      case v:ArrayType =>
        val size = rnd.nextInt(10)
        JArray(
          (0 to size).map(_ => randomJson(rnd, v.elementType)).toList
        )
      case v:StructType =>
        JObject(
          v.fields.flatMap{
            f =>
              if( f.nullable && rnd.nextBoolean())
                None
              else
                Some(JField(f.name, randomJson(rnd, f.dataType)))
          }.toList
        )
    }

  }
}
