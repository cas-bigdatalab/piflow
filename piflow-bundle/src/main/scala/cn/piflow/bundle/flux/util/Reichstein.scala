package cn.piflow.bundle.flux.util

import org.apache.spark.mllib.stat.Statistics
import org.apache.spark.rdd.RDD
import org.apache.spark.sql.functions.{col, max, min}
import org.apache.spark.sql.{DataFrame, SparkSession}

import scala.collection.mutable.ArrayBuffer

/**
 * 异常值处理：u*校正，reichstein法
 *
 * @Author renhao
 * @Description:
 * @Data 2023/2/23 16:15
 * @Modified By:
 */
class Reichstein extends Serializable{

  //  val spark = SparkSession.builder()
  //    .master("local[*]")
  //    .appName("dataCompare")
  //    .config("spark.sql.caseSensitive", "true")
  //    .enableHiveSupport()
  //    .getOrCreate()
  //
  //  val metroCBS = MetroExcel(spark)
  //  val fluxCBS = CBSExcel(spark)
  //  val metroJoinFlux = metroCBS.join(fluxCBS, Seq("year", "month", "day", "hour"), "left")

//  def main(args: Array[String]): Unit = {
//    //    val metroJoinFlux = metroCBS.join(fluxCBS, Seq("year", "month", "day", "hour"), "left")
//    //    //5cm土壤温度m5
//    //    val soilTemperatureField = "Ts_107_1_AVG"
//    //    //摩擦风速字段，即U*
//    //    val FrictionWindSpeedField = "p5"
//    //    //FC值 CO2通量 NEE
//    //    val FC = "p1"
//    //    val flagValue = -99999
//    //    //设置通量百分比
//    //    val percentFlux = 0.99
//    //    reichsteinCorrectU(metroJoinFlux,soilTemperatureField,FrictionWindSpeedField,FC,flagValue,percentFlux).show()
//  }


  //综合6个温度组的U*Cg值计算这个数据集的u*c值并校正U*
  def reichsteinCorrectU(spark: SparkSession, metroJoinFlux: DataFrame, soilTemperatureField: String, FrictionWindSpeedField: String
                         , FC: String, flagValue: Integer, percentFlux: Double): DataFrame = {
    metroJoinFlux.createOrReplaceTempView("temp")
    spark.sql(
      s"""
         |select year,month,hour,day_status
         |,row_number() over(order by ${soilTemperatureField}) as orderNumber
         |,${soilTemperatureField},${FrictionWindSpeedField},${FC} from temp
         |""".stripMargin).createOrReplaceTempView("metroJoinFluxOrderByTem")
    val total = metroJoinFlux.count()
    val groupNumber = metroJoinFlux.count() / 6
    val arrUCG = new ArrayBuffer[Double]()
    for (index <- 1 to 6) {
      var metroJoinFluxGroup: DataFrame = null
      if (index < 6) {
        metroJoinFluxGroup = spark.sql(
          s"""
             |select * from metroJoinFluxOrderByTem where orderNumber > ${index - 1}*${groupNumber}
             |and orderNumber <= ${index}*${groupNumber}
             |""".stripMargin)
      } else {
        metroJoinFluxGroup = spark.sql(
          s"""
             |select * from metroJoinFluxOrderByTem where orderNumber > 5*${groupNumber}
             |and orderNumber <= ${total}
             |""".stripMargin)
      }
      if (pearson(metroJoinFluxGroup, soilTemperatureField, FrictionWindSpeedField) < 0.4) {
        arrUCG.append(calculateCriticalValue(spark,metroJoinFluxGroup, FrictionWindSpeedField, FC, flagValue, percentFlux))
      }
    }
    if (arrUCG.filterNot(_ == flagValue).length < 1) {
      throw new Exception("not found U*C")
    }
    //    综合6个温度组的U*Cg值计算这个数据集的u*c值
    val Uc = median(arrUCG)
    val cols = metroJoinFlux.schema.map(_.name).map(x => {
      if (x == FC) {
        s"case when ${FrictionWindSpeedField}<$Uc and day_status='night' then $flagValue else ${FC} end as $FC"
      } else {
        x
      }
    }).mkString(",")
    spark.sql(
      s"""
         |select $cols from temp
         |""".stripMargin)
  }

  //求集合中位数
  def median(arr: ArrayBuffer[Double]): Double = {
    val arrOrder = arr.sorted
    if (arr.length % 2 == 1) {
      arrOrder(arrOrder.length / 2)
    } else {
      (arrOrder(arrOrder.length / 2) + arrOrder(arrOrder.length / 2 - 1)) / 2
    }
  }

  //计算每个温度组的临界值
  def calculateCriticalValue(spark: SparkSession,metroJoinFluxGroup: DataFrame, FrictionWindSpeedField: String
                             , FC: String, flagValue: Integer, percentFlux: Double): Double = {
    metroJoinFluxGroup.createOrReplaceTempView("metroJoinFluxGroup")
    val u_max = metroJoinFluxGroup.select(col(FrictionWindSpeedField).cast("Double").as(FrictionWindSpeedField))
      .select(max(FrictionWindSpeedField))
      .rdd.map(_.get(0).asInstanceOf[Double]).collect()(0)
    val u_min = metroJoinFluxGroup.select(col(FrictionWindSpeedField).cast("Double").as((FrictionWindSpeedField)))
      .select(min(FrictionWindSpeedField))
      .rdd.map(_.get(0).asInstanceOf[Double]).collect()(0)
    val u_D_value = (u_max - u_min) / 20
    for (index <- 1 to 20) {
      val metroJoinFluxGroupSub = spark.sql(
        s"""
           |select $FC,$FrictionWindSpeedField from metroJoinFluxGroup where $FrictionWindSpeedField >= ($index-1)*$u_D_value+$u_min

          |and $FrictionWindSpeedField < $index * $u_D_value+$u_max

          |""".stripMargin)
      //从第index+1个u*小组开始计算该温度组的FC均值
      val FC_AVG_index: Double = spark.sql(
        s"""
           |select avg(cast($FC as double))
           |from metroJoinFluxGroup
           |where $FrictionWindSpeedField >= $index*$u_D_value+$u_min
           |""".stripMargin).rdd.map(_.get(0).asInstanceOf[Double]).collect()(0)
      metroJoinFluxGroupSub.select(col(FC).cast("Double"),col(FrictionWindSpeedField) ).rdd
        .map(x=>(x.get(0) .asInstanceOf[Double],x.get(1).toString.toDouble)) .collect().foreach(x=>{
        if(x._1 > FC_AVG_index *percentFlux){
          return x._2
        }
      })
    }
    flagValue.toDouble
  }


  //计算dataframe中某两列的皮尔逊相关系数
  def pearson( df:DataFrame ,col1 :String,col2:String): Double ={
    val seriesX: RDD[Double] = df.select(col1).rdd.map(_.get(0).toString.toDouble)
    val seriesY: RDD[Double] = df.select(col2).rdd.map(_.get(0).toString.toDouble)
    val correlation: Double = Statistics.corr(seriesX, seriesY, "pearson")
    correlation
  }

}
