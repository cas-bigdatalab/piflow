package cn.piflow.bundle.flux.util

import cn.piflow.bundle.flux.util.CommonUtil.SunriseAndSunsetTime
import org.apache.spark.sql.expressions.Window
import org.apache.spark.sql.functions.row_number
import org.apache.spark.sql.types.{DoubleType, IntegerType}
import org.apache.spark.sql.{DataFrame, SparkSession}

import scala.collection.mutable.ArrayBuffer



class FluxUtil_1 extends Serializable {

  /**
   * 单一字段阈值替换 ，不符合需求的数据 ，用标识位赋值 （包含上下限）
   *
   * @param spark
   * @param originDF
   * @param fields              要清洗的字段,多个以逗号分隔
   * @param maxValue            阈值上限
   * @param minValue            阈值下限
   * @param flagValue           标识位赋值，不符合条件
   * @param additionalCondition 标识位赋值，不符合条件
   * @return
   */
  def singleFieldThresholdCleaning(spark: SparkSession, originDF: DataFrame, fields: String, maxValue: String, minValue: String, flagValue: String, additionalCondition: String): DataFrame = {

    val thresholdReplaceSqlBuilder = new StringBuilder()
    originDF.schema.fieldNames.foreach(x => {
      if (fields.split(",").contains(x)) {
//        val str = s"if(`${x}` <= ${maxValue.toDouble} and `${x}` >= ${minValue.toDouble} ,`${x}`,'${flagValue}' ) as `${x}`"
        val str = s"if(`${x}` <= ${maxValue.toDouble} and `${x}` >= ${minValue.toDouble} and ${additionalCondition} ,`${x}`,'${flagValue}' ) as `${x}`"
        thresholdReplaceSqlBuilder.append(str + ",")
      } else {
        thresholdReplaceSqlBuilder.append("`" + x + "`,")
      }
    })

    spark.catalog.dropTempView("singleDF")
    originDF.createOrReplaceTempView("singleDF")

    val sqlStr = s"select ${thresholdReplaceSqlBuilder.stripSuffix(",")}  from singleDF"
    println(sqlStr)
    val resultDF = spark.sql(sqlStr)

    spark.sql("show tables").show()
    resultDF
  }


  /**
   * 批量阈值替换 根据阈值表中的数据，不符合需求的数据 ，用标识位赋值（包含上下限）
   *
   * @param spark
   * @param originDF
   * @param thresholdDF 阈值表： schema 需包含 field ,min_value ,max_value,flagValue 字段
   * @param flagValue   标识位赋值，不符合条件
   * @return
   */
  def batchFieldThresholdCleaning(spark: SparkSession, originDF: DataFrame, thresholdDF: DataFrame): DataFrame = {
    //    阈值表中的所有字段名
    val thresholdFields: ArrayBuffer[String] = new ArrayBuffer[String]()

    thresholdDF.select("field").collect().foreach(x => {
      thresholdFields.append(x.toString.toLowerCase.trim)
    })

    val thresholdReplaceSqlBuilder = new StringBuilder()
    originDF.schema.fieldNames.foreach(x => {
      if (thresholdFields.contains(x.toLowerCase)) {
        val minValue = thresholdDF.where(s"field = '${x}'").select("min_value").first().get(0).toString.toDouble
        val maxValue = thresholdDF.where(s"field = '${x}'").select("max_value").first().get(0).toString.toDouble
        val flagValue = thresholdDF.where(s"field = '${x}'").select("flag_value").first().get(0).toString
        val str = s"if(`${x}` <= ${maxValue} and `${x}` >= ${minValue} ,`${x}`,'${flagValue}' ) as `${x}`"
        thresholdReplaceSqlBuilder.append(str + ",")
      } else {
        thresholdReplaceSqlBuilder.append("`" + x + "`,")
      }
    })

    spark.catalog.dropTempView("batchFieldDF")
    originDF.createOrReplaceTempView("batchFieldDF")
    val sqlStr = s"select ${thresholdReplaceSqlBuilder.stripSuffix(",")}  from batchFieldDF "
    val resultDF = spark.sql(sqlStr)

    resultDF
  }


  /**
   * 根据年月日小时及 日的id 添加 当前时间的状态【白天或者黑夜（按照日出日落时间定义）】
   *
   * @param spark
   * @param originDF  schema 必须包含 year ,month ,day, day_id(按照日期递增的 id)
   * @param longitude 经度
   * @param latitude  维度
   * @return
   */
  def AddDayStateWithDayHour(spark: SparkSession, originDF: DataFrame, longitude: Double, latitude: Double): DataFrame = {
    //    val longitude:Double = 128.1
    //    val latitude:Double  = 42.4

    spark.udf.register("SunriseAndSunset", (id: String) => {
      SunriseAndSunsetTime(longitude, latitude, id.toInt);
    })
    originDF.createOrReplaceTempView("addDayStateWithDayHour")
    val resultDF = spark.sql(
      """
        |select if(cast(hour as double)>split(SunriseAndSunset(day_id),',')[0]
        |       and cast(hour as double)<split(SunriseAndSunset(day_id),',')[1],'day','night')  as day_status
        |  ,*
        | from addDayStateWithDayHour
        |""".stripMargin)

    resultDF
  }


  /**
   * 按照时间日期 ，新增 day_id 字段 (按照日期递增的 id)
   *
   * @param spark
   * @param originDF schema 必须包含 year ,month ,day
   * @return
   */
  def AddIdWithDay(spark: SparkSession, originDF: DataFrame,partitionNum:Int): DataFrame = {

    import spark.sqlContext.implicits._
    val df_id = originDF.withColumn("year",$"year".cast(IntegerType))
      .withColumn("month",$"month".cast(IntegerType))
      .withColumn("day",$"day".cast(IntegerType))
      .withColumn("hour",$"hour".cast(DoubleType))

    val spec_id = Window.partitionBy().orderBy("year", "month", "day","hour")
    val df_id_1= df_id.withColumn("id",row_number().over(spec_id))

    val df_day_id = df_id.select("year","month","day").distinct()
    val spec_day_id = Window.partitionBy().orderBy("year", "month", "day")
    val df_day_id_1= df_day_id.withColumn("day_id",row_number().over(spec_day_id))


    // 给通量数据，按照时间日期 ，新增 id 字段
    val resultDF = df_id_1.join(df_day_id_1, Seq("year", "month", "day"),"left")
      .repartition(partitionNum)
    resultDF
  }

}
