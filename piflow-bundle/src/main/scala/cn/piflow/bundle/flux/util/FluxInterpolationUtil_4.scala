package cn.piflow.bundle.flux.util

import org.apache.spark.sql.{DataFrame, SparkSession}

/**
 *  通量数据插补
 */

class FluxInterpolationUtil_4 {


  /**
   * 插补算法： MDV-I：固定窗口
   * 平均日变化法（MDV）/半经验方法
   * @param spark
   * @param originDF schema 必须包含 hour, day_id(按照日期递增的 id)
   * @param fields   需要插补的字段，多个以逗号分隔
   * @param mdv_num  窗口时间
   * @param flagValue  质量控制标识
   * @return
   */
  def MDVFixed(spark:SparkSession,originDF:DataFrame,fields:String,mdv_num:Int,flagValue:Int):DataFrame={
    spark.catalog.dropTempView("MDVFixed")
    originDF.createOrReplaceTempView("MDVFixed")
//  根据窗口 对通量数据进行分区
    val dayZoneDF = spark.sql(s"select * ,ceiling(day_id/${mdv_num}) as zone from MDVFixed")
    dayZoneDF.createOrReplaceTempView("dayZoneDF")

    val zoneAvgSqlBuilder = new StringBuilder()
    val supplementSqlBuilder = new StringBuilder()

    var df = originDF
    fields.split(",").foreach(field => {
      // 统计每个分区的平均数
      val zoneAvgStr = s"round(avg(if(${field} > ${flagValue},${field},0)),5) as `${field}`"
      zoneAvgSqlBuilder.append(zoneAvgStr+",")
      // 插补无效值为分区平均值
      val supplementStr= s"if( a.${field} > ${flagValue},a.${field},b.`${field}`) as `${field}`"
      supplementSqlBuilder.append(supplementStr+",")

      df = originDF.drop(field)
    })

//    插补计算
    val interpolationCalculationDF = spark.sql(
      s"""
         | select day_id,a.hour ,${supplementSqlBuilder} a.zone from dayZoneDF a
         | left join (
         |       select ${zoneAvgSqlBuilder} zone,hour  from dayZoneDF group by zone,hour
         |    )b
         | on a.zone =b.zone and a.hour= b.hour
         |""".stripMargin)

    val resultDF=df.join(interpolationCalculationDF,Seq("day_id","hour"))

    resultDF
  }


  /**
   * 插补算法： MDV-G：滑动窗口
   * 平均日变化法（MDV）/半经验方法
   * @param spark
   * @param originDF schema 必须包含 hour, day_id(按照日期递增的 id)
   * @param field
   * @param mdv_num  窗口时间 ，必须为奇数
   * @param flagValue  质量控制标识
   * @return
   */
  def MDVSliding(spark:SparkSession,originDF:DataFrame,fields:String,mdv_num:Int,flagValue:Int):DataFrame={
    //  根据窗口时间计算前后间隔
    val day_range= math.floor(mdv_num / 2.0).toInt
    println("滑动窗口前后间隔时间--->"+day_range)

    spark.catalog.dropTempView("mdvSlidingDF")
    originDF.createOrReplaceTempView("mdvSlidingDF")

    val builder: StringBuilder = new StringBuilder
    val avgBuilder: StringBuilder = new StringBuilder
    fields.split(",").foreach(x=>{
      builder.append(s"b.${x} as ${x} ,")
      avgBuilder.append(s"round( if( sum(if(${x}= ${flagValue},0,1)) = 0, ${flagValue}, sum(if(${x}= ${flagValue},0,${x})) / sum(if(${x}= ${flagValue} ,0,1)) ),5) as  ${x} ,")

    })

    val avgWindowsDF = spark.sql(
      s"""
          | select day_id,hour, ${avgBuilder.stripSuffix(",")}    from (
          |   select a.day_id,a.hour,${builder.stripSuffix(",")}  from mdvSlidingDF a
          |   left join mdvSlidingDF b
          |   on a.day_id >= b.day_id-${day_range} and a.day_id <= b.day_id+${day_range} and a.day_id<>b.day_id  and a.hour=b.hour
          |) a group by day_id,hour
          |""".stripMargin)

    avgWindowsDF.createOrReplaceTempView("avgWindowsDF")
    val resultBuilder: StringBuilder = new StringBuilder
    originDF.schema.fieldNames.foreach(x=>{
      if(fields.split(",").contains(x)) resultBuilder.append(s" if(b.${x} is not null and a.${x} = ${flagValue},b.${x},a.${x}) as ${x} ,")
      else resultBuilder.append(s"a.${x} ,")
    })

    val MDVSlidingDF = spark.sql(
      s"""
        |
        | select ${resultBuilder.stripSuffix(",")} from  mdvSlidingDF a
        | left join avgWindowsDF b
        | on a.day_id = b.day_id  and a.hour = b.hour
        |
        |""".stripMargin)

    MDVSlidingDF
  }

  def MDVSliding_old(spark:SparkSession,originDF:DataFrame,field:String,mdv_num:Int,flagValue:Int):DataFrame={
    //  根据窗口时间计算前后间隔
    val day_range= math.ceil(mdv_num / 2.0).toInt

    spark.catalog.dropTempView("originDF")
    originDF.repartition(30).createOrReplaceTempView("originDF")
    println(originDF.rdd.getNumPartitions)

    //    插补计算
    val resultDF = spark.sql(
      s"""
         |select a.day_id,a.hour,if(b.avg_num is not null,b.avg_num,a.${field}) as `${field}`  from originDF a
         |left join (
         |    select day_id,hour, avg(${field}) as avg_num from (
         |          select a.day_id,a.hour, b.${field}  from (select * from originDF where ${field} = ${flagValue})a
         |          left join originDF  b
         |          on a.day_id >= b.day_id-${day_range} and a.day_id <= b.day_id+${day_range} and a.day_id<>b.day_id  and a.hour=b.hour
         |      )a where ${field} <> ${flagValue} group by day_id,hour
         |)b on a.day_id=b.day_id and a.hour=b.hour
         |""".stripMargin)

    //    val resultDF= originDF.drop(field).join(interpolationCalculationDF,Seq("day_id","hour"))

    resultDF
  }



  /**
   * 间隔插补1：----------------------------------------
   * 当前值无效M（k），前后为有效值M（k-1)、M(k+1），当前值 为 M(k)=(M（k-1)+M(k+1）)/2.0
   * @param spark
   * @param originDF schema 必须包含 hour, day_id(按照日期递增的 id)
   * @param field 需要进行插补的字段,多個字段以逗號分隔
   * @param flagValue 质量控制标记值:Quality control marker value
   * @return
   */
  def ForwardAndBackwardInterpolation(spark:SparkSession,originDF:DataFrame,fields: String,flagValue:Int):DataFrame ={

    val schemaFieldNames = originDF.schema.fieldNames

    val avgString = new StringBuilder
    val compareString = new StringBuilder

    schemaFieldNames.foreach(x=>{
      if(fields.split(",").contains(x)){
        avgString.append(s"if(a.${x}= ${flagValue} or b.${x}= ${flagValue} ,${flagValue},round((a.${x}+b.${x})/2,5) ) as ${x} ,")
        compareString.append(s"if(a.${x} = ${flagValue} and b.${x}<> ${flagValue},b.${x},a.${x}) as ${x} ,")
      } else {
        avgString.append(s"a.${x} ,")
        compareString.append(s"a.${x} ,")
      }
    })

    originDF.createOrReplaceTempView("originDF")
    val frontAndBackAverage = spark.sql(
      s"""
         |select  a.day_id+1 as day_id_b,${avgString.stripSuffix(",")}   from originDF  a
         |left join originDF b
         |on a.day_id=b.day_id-2 and a.hour = b.hour
         |""".stripMargin)
    frontAndBackAverage.createOrReplaceTempView("frontAndBackAverage")

    val resultDF = spark.sql(
      s"""
         |select ${compareString.stripSuffix(",")}  from originDF a
         |left join frontAndBackAverage b
         | on a.day_id=b.day_id_b and a.hour = b.hour
         |
         |""".stripMargin)
    resultDF
  }



  /**
   * 间隔插补1：
   * 当前值无效M（k），前后为有效值M（k-1)、M(k+1），当前值 为 M(k)=(M（k-1)+M(k+1）)/2.0
   * @param spark
   * @param originDF schema 必须包含 hour, day_id(按照日期递增的 id)
   * @param field 需要进行插补的字段
   * @param flagValue 质量控制标记值:Quality control marker value
   * @return
   */
  def ForwardAndBackwardInterpolation_bak(spark:SparkSession,originDF:DataFrame,field: String,flagValue:Int):DataFrame ={

    originDF.select("day_id","hour",field).createOrReplaceTempView("originDF")
    //    查询出当前值无效的数据 及其前后的数据
    val CurrentValueIsInvalidDF = spark.sql(
      s"""
         |select a.day_id ,a.hour,b.${field} from  (select * from originDF where ${field}=${flagValue})a
         | left join originDF b on (a.day_id = b.day_id-1 or a.day_id = b.day_id+1 ) and a.hour=b.hour and a.day_id<>b.day_id and b.${field}<>${flagValue}
         |""".stripMargin)
    CurrentValueIsInvalidDF.createOrReplaceTempView("CurrentValueIsInvalidDF")

//    CurrentValueIsInvalidDF.orderBy("day_id","hour").show(100)


    //    过滤前后为有效值的数据，然后求平均数 ，替换原始无效值
    val MeetTheConditionsDF = spark.sql(
      s"""
         |select a.day_id,a.hour,if(b.avg_num is not null,b.avg_num,a.${field}) as `${field}` from originDF a
         |left join (
         |     select day_id,hour,avg(${field}) as avg_num from (
         |            select * from CurrentValueIsInvalidDF where concat(day_id,hour) in  (select concat(day_id,hour)  from CurrentValueIsInvalidDF
         |             group by day_id ,hour having count(*)>1 )
         |     ) group by day_id,hour
         |)b on a.day_id=b.day_id and a.hour=b.hour
         |""".stripMargin)

    val resultDF =  originDF.drop(field).join(MeetTheConditionsDF,Seq("day_id","hour"))

    resultDF
  }


  /**
   * 间隔插补2：
   * 当前值无效M（k），M（k+1）无效，M（k-1）有效、M（k+2）有效
   * M(k)=M(k-1)+ abs(M(k-1)-M(k+2))/3
   * M(k+1)=M(k-1)+ abs(M(k-1)-M(k+2))*2/3
   * @param spark
   * @param originDF schema 必须包含 hour, day_id(按照日期递增的 id)
   * @param field  需要进行插补的字段
   * @param flagValue  质量控制标记值:Quality control marker value
   * @return
   */
  def CurrentAndPostValueInterpolation(spark:SparkSession,originDF:DataFrame,fields: String,flagValue:Int):DataFrame ={

    val interpolation = new InterpolationMetro
    val interpolationResultDF = interpolation.imputationReplacement(spark,originDF,fields,24*3600,flagValue)

    interpolationResultDF
  }




}
