package cn.piflow.bundle.common

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.SparkSession

class FieldTypeConversion extends ConfigurableStop{
  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "字段类型转换"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] =  List(Port.DefaultPort)

  var doubleTypeField: String = _
  var intTypeField: String = _
  var decimalTypeField: String = _
  var decimalTypePrecision: String = _

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val originDF = in.read()

    var doubleTypeStrings: Array[String] = Array[String]("double类型转换传入字段为空")
    var integerTypeStrings: Array[String] = Array[String]("int类型转换传入字段为空")
    var decimalTypeStrings: Array[String] = Array[String]("decima类型转换传入字段为空")

    if(doubleTypeField != null){
      doubleTypeStrings  = doubleTypeField.toLowerCase.split(",")
    }
    if(intTypeField != null){
       integerTypeStrings = intTypeField.toLowerCase.split(",")
    }
    if(decimalTypeField != null){
      decimalTypeStrings = decimalTypeField.toLowerCase.split(",")
    }

    val builder = new StringBuilder
    originDF.schema.fieldNames.foreach(x=>{
      if (doubleTypeStrings.contains(x.toLowerCase)) {
        builder.append(s"cast(${x} as double) as $x ,")
      } else if(integerTypeStrings.contains(x.toLowerCase)) {
        builder.append(s"cast(${x} as integer) as $x ,")
      } else if(decimalTypeStrings.contains(x.toLowerCase)) {
        builder.append(s"cast(${x} as ${decimalTypePrecision}) as $x ,")
      }else{
        builder.append(s"${x}  ,")
      }
    })

    originDF.createOrReplaceTempView("originDF")
    val typeConversion_sql_str = s"select ${builder.stripSuffix(",")}  from originDF  "
    val typeConversionDF  = spark.sql(typeConversion_sql_str)

    typeConversionDF.printSchema()
    out.write(typeConversionDF)

  }

  override def setProperties(map: Map[String, Any]): Unit = {
    doubleTypeField=MapUtil.get(map,"doubleTypeField").asInstanceOf[String]
    intTypeField=MapUtil.get(map,"intTypeField").asInstanceOf[String]
    decimalTypeField=MapUtil.get(map,"decimalTypeField").asInstanceOf[String]
    decimalTypePrecision=MapUtil.get(map,"decimalTypePrecision").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val doubleTypeField = new PropertyDescriptor()
      .name("doubleTypeField")
      .displayName("doubleTypeField")
      .description("转换为double类型的字段,多个以逗号分隔")
      .defaultValue("")
      .required(true)
      .example("")
    descriptor = doubleTypeField :: descriptor

    val intTypeField = new PropertyDescriptor()
      .name("intTypeField")
      .displayName("intTypeField")
      .description("转换为 int 类型的字段，多个以逗号分隔")
      .defaultValue("")
      .required(true)
      .example("")
    descriptor = intTypeField :: descriptor

    val decimalTypeField = new PropertyDescriptor()
      .name("decimalTypeField")
      .displayName("decimalTypeField")
      .description("转换为精度更高的十进制类型的字段，多个以逗号分隔")
      .defaultValue("")
      .required(true)
      .example("")
    descriptor = decimalTypeField :: descriptor

    val decimalTypePrecision = new PropertyDescriptor()
      .name("decimalTypePrecision")
      .displayName("decimalTypePrecision")
      .description("DECIMAL类型精度要求：DECIMAL(20, 10)中表示一个 DECIMAL 类型，该类型总共有 20 位数字，其中 10 位是小数部分")
      .defaultValue("DECIMAL(20, 10)")
      .required(true)
      .example("DECIMAL(20, 10)")
    descriptor = decimalTypeField :: descriptor


    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/csv/CsvParser.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.CommonGroup)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

}
