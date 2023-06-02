package cn.piflow.bundle.flux.util

import cn.piflow.bundle.flux.util.CommonUtil.toTimeStamp
import org.apache.spark.sql.functions.col
import org.apache.spark.sql.{DataFrame, SparkSession}

/**
 * 异常值处理
 */
class FluxOutlierHandlingUtil_3 extends Serializable {

  /**
   * 异常值处理：同期降雨数据剔除
   *  降水的发生扰乱了生态系统中正常的大气流动，并导致仪器失灵，
   *  因此需要剔除掉降水同期观测数据，以保证数据质量
   * @param spark
   * @param metroCBS  气象数据
   * @param fluxCBS   通量数据
   * @param fields  通量数据中需要处理的字段，多个以逗号分隔
   * @param rainFallField  气象数据降雨量  Rain_0_TOT
   * @param flagValue 质量控制标识
   * @return
   */
  def RainfallDataCulling(spark:SparkSession,metroCBS:DataFrame,fluxCBS:DataFrame,fields:String,rainFallField:String,flagValue:Int): DataFrame = {
    spark.udf.register("toTimeS",toTimeStamp _)

    val metroJoinFlux = fluxCBS.as("a").join(metroCBS.as("b"), Seq("year", "month", "day", "hour"), "left")
      .select(col("a.*"),col(s"b.${rainFallField}"))

    spark.catalog.dropTempView("temp")
    metroJoinFlux.createOrReplaceTempView("temp")
    val firstPhaseCols = metroJoinFlux.schema.map(x => {
      if (fields.split(",").map(_.toLowerCase).contains(x.name.toLowerCase)) {
        flagValue + " " + x.name
      } else {
        x.name
      }
    }).mkString(",")
    spark.sql(
      s"""
         |select $firstPhaseCols,toTimes(year,month,day,hour) as timestamp from temp where cast(${rainFallField} as double) > 0
         |union all
         |select temp.*,toTimes(year,month,day,hour) as timestamp from temp where cast(${rainFallField} as double) <= 0
         |""".stripMargin).createOrReplaceTempView("pwin_temp")

//    println(spark.sql("select * from pwin_temp").count())
    spark.sql(s"select toTimes(year,month,day,hour)+1800*1000 as timestamp,${fields} from pwin_temp where cast(${rainFallField} as double) > 0")
      .createOrReplaceTempView("pwin_1_temp")

    val secondPhaseCols = metroJoinFlux.schema.map(x => {
      if (fields.split(",").map(_.toLowerCase).contains(x.name.toLowerCase())) {
        s"case when b.${x.name} is null then a.${x.name} else b.${x.name} end as ${x.name}"
      } else {
        "a." + x.name
      }
    }).mkString(",")

    val resultDF = spark.sql(
      s"""
         |select $secondPhaseCols
         |from pwin_temp a left join pwin_1_temp b on
         |a.timestamp=b.timestamp
         |""".stripMargin)

    resultDF.drop(col(rainFallField))
  }


  /**
   *  异常值处理：通量野点剔除（固定窗口）
   * 方差/标准差法
   * 采用 固定窗口方式， 在指定大小窗口内，计算标准差或方差，
   * 对超过 x 倍方差或标准差的数据，质量控制标识为 Ao并剔除之。
   * @param spark
   * @param originDF  schema 必须包含id ,自增字段
   * @param fields    需要野点剔除的字段，多个以逗号分隔
   * @param mdv_num   窗口时间
   * @param multiple   倍数
   * @param statisticalType  计算类型,方差或标准差的 （stddev,variance）
   * @param flagValue   质量控制标识
   * @return
   */
  def FluxOutfieldEMDVFixed(spark:SparkSession,originDF:DataFrame,field:String,mdv_num:Int,multiple:Double,statisticalType:String,flagValue:String):DataFrame={
    val statisticalType = "stddev"
//    val statisticalType = "variance"
//    val statisticalType = "avg"
//    val multiple = "1"
//    val flagValue = -99999

    spark.catalog.dropTempView("fixedDF")
    originDF.createOrReplaceTempView("fixedDF")

    //  根据窗口 对通量数据进行分区
    val fixZoneDF = spark.sql(s"select * ,ceiling(id/${mdv_num}) as zone from fixedDF")
    fixZoneDF.createOrReplaceTempView("fixZoneDF")

//     统计各个分区内的 阈值
    val zoneStatisticalDF  = spark.sql(
      s"""
        | select zone
        |       ,round( avg($field) - ($statisticalType($field) * $multiple )         ,5) as   min_value_flag
        |       ,round( avg($field) + ($statisticalType($field) * $multiple )         ,5) as   max_value_flag
        | from  ( select * from fixZoneDF where $field <> ${flagValue} )a
        | group by zone
        |""".stripMargin)
    zoneStatisticalDF.createOrReplaceTempView("zoneStatisticalDF")

    val outfieldEMDVSqlBuilder = new StringBuilder()
    fixZoneDF.schema.fieldNames.foreach(x=>{
      if(x.toLowerCase.equals(field.toLowerCase)){
        // 符合条件的数据 ，进行插补替换 （超出阈值范围的数据标记为异常并剔除）
        val supplementStr= s"if( a.${field} >= min_value_flag and a.${field}<= max_value_flag , a.$field , $flagValue ) as `${field}`"
        outfieldEMDVSqlBuilder.append(supplementStr + ",")
      } else {
        outfieldEMDVSqlBuilder.append(s"a.$x,")
      }
    })

    val outfieldResultDF = spark.sql(
      s"""
        |select ${outfieldEMDVSqlBuilder.stripSuffix(",")}  from fixZoneDF a
        |left join zoneStatisticalDF b
        |on a.zone =b.zone
        |""".stripMargin).drop("zone")

    outfieldResultDF
  }


  /**
   *  异常值处理：通量野点剔除（滑动窗口）
   * 方差/标准差法
   * 采用滑动窗口方式， 在指定大小窗口内，计算标准差或方差，
   * 对超过 x 倍方差或标准差的数据，质量控制标识为 Ao并剔除之。
   * @param spark
   * @param originDF  schema 必须包含 id(按照日期递增的 id)
   * @param fields    需要野点剔除的字段，多个以逗号分隔
   * @param mdv_num   窗口时间
   * @param multiple   倍数
   * @param statisticalType  计算类型,方差或标准差的 （stddev,variance）
   * @param flagValue  质量控制标识
   * @return
   */
  def FluxOutfieldEliminationMDVSliding(spark:SparkSession,originDF:DataFrame,field:String,mdv_num:Int,multiple:Double,statisticalType:String,flagValue:String):DataFrame={
    //    val statisticalType = "stddev"
    //    val statisticalType = "variance"
    //  根据窗口时间计算前后间隔
    val windows_range= math.floor(mdv_num / 2.0).toInt
    println("滑动窗口前后间隔时间--->"+windows_range)

    spark.catalog.dropTempView("outfieldMdvSlidingDF")
    originDF.createOrReplaceTempView("outfieldMdvSlidingDF")


    val singleStatisticalDF =  spark.sql(
      s"""
        |select id,
        |       ,round( avg($field) - ($statisticalType($field) * $multiple )         ,5) as   min_value_flag
        |       ,round( avg($field) + ($statisticalType($field) * $multiple )         ,5) as   max_value_flag
        | from (
        |   select a.id,b.$field   from outfieldMdvSlidingDF a
        |   left join outfieldMdvSlidingDF b
        |   on a.id >=b.id- $windows_range and a.id <= b.id+$windows_range and a.id<>b.id
        |   where contrast_flag<> $flagValue
        | ) group by id
        |""".stripMargin)

    singleStatisticalDF.createOrReplaceTempView("singleStatisticalDF")


    val outfieldEMDVSlidingSqlBuilder = new StringBuilder()
    originDF.schema.fieldNames.foreach(x=>{
      if(x.toLowerCase.equals(field.toLowerCase)){
        // 符合条件的数据 ，进行插补替换 （超出阈值范围的数据标记为异常并剔除）
        val supplementStr= s"if( a.${field} >= min_value_flag and a.${field}<= max_value_flag , a.$field , $flagValue ) as `${field}`"
        outfieldEMDVSlidingSqlBuilder.append(supplementStr + ",")
      } else {
        outfieldEMDVSlidingSqlBuilder.append(s"a.$x,")
      }
    })

    val outfieldMDVSlidingResultDF = spark.sql(
      s"""
         |select ${outfieldEMDVSlidingSqlBuilder.stripSuffix(",")}  from outfieldMdvSlidingDF a
         |left join singleStatisticalDF b
         |on a.id =b.id
         |""".stripMargin)


    outfieldMDVSlidingResultDF

  }

  /**
   * 异常值处理：通量野点剔除 差分法
   * @param spark
   * @param originDF
   * @param rowName       修改通量字段名称
   * @param para_Z        人为定义的敏感性，z越大敏感性越低，剔除的数据也越少。参考取值为: 4，5.5，7
   * @param flagValue     标识位赋值，不符合条件
   * @return
   */
  def FluxDifference(spark: SparkSession, originDF: DataFrame, rowName: String, para_Z: Double, flagValue: String): DataFrame = {

    val para: Double = 0.6475
    val invalid_flag = flagValue.toDouble

    spark.catalog.dropTempView("temp")
    originDF.createOrReplaceTempView("originDiffDF")


    originDF
  }











}
