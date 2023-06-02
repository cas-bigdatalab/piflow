package cn.piflow.bundle.flux.util

import cn.piflow.bundle.FluxJavaUtil.Theleastsquaremethod
import org.apache.spark.sql.functions.monotonically_increasing_id
import org.apache.spark.sql.{DataFrame, Row, SparkSession}

import scala.collection.mutable.ArrayBuffer

class FluxDataCorrectionUtil_2 extends Serializable {
  val fluxDataCorrection = new FluxDataCorrectionUtil_2_Util

//  二次坐标旋转（DR）

  /**
   * 二次坐标旋转（DR）
   * @param spark
   * @param originDF
   * @param FcField    Fc         :  CO2通量
   * @param LeField    Le         :  潜热通量
   * @param HsField    Hs         :  显热通量
   * @param u_starField    u_star         :  摩擦风速
   * @param p06        cov_Uz_Uz	:  垂直风速方差
   * @param p07        cov_Uz_Ux	:  垂直风速与X方向风速协方差
   * @param p08        cov_Uz_Uy	:  垂直风速与Y方向风速协方差
   * @param p09        cov_Uz_co2 :  垂直风速与CO2密度协方差
   * @param p10        cov_Uz_h2o :  垂直风速与H2O密度协方差
   * @param p11        cov_Uz_Ts  :  垂直风速与温度协方差
   * @param p12        cov_Ux_Ux	:  X方向风速方差	p12
   * @param p13        cov_Ux_Uy	:  X与Y方向风速协方差
   * @param p14        cov_Ux_co2 :  X方向风速与CO2密度协方差
   * @param p15        cov_Ux_h2o :  X方向风速与H2O密度协方差
   * @param p16        cov_Ux_Ts  :  X方向风速与温度协方差
   * @param p17        cov_Uy_Uy	:  Y方向风速方差
   * @param p18        cov_Uy_co2 :  Y方向风速与CO2密度协方差
   * @param p19        cov_Uy_h2o :  Y方向风速与H2O密度协方差
   * @param p20        cov_Uy_Ts  :  Y方向风速与温度协方差
   * @param p24        Ux_Avg     :  X方向平均风速
   * @param p25        Uy_Avg     :  Y方向平均风速
   * @param p26        Uz_Avg     :  Z方向平均风速
   * @return
   */
    def DRCoordinateRotationUtil(spark:SparkSession,originDF:DataFrame,FcField:String,LeField:String,HsField:String,u_starField:String
                                ,p06:String,p07:String,p08:String,p09:String,p10:String,p11:String,p12:String,p13:String,p14:String,p15:String,p16:String,p17:String,
                                 p18:String,p19:String,p20:String,
                                 p24:String,p25:String,p26:String):DataFrame={

      spark.udf.register("DrUdf" ,(p06:String,p07:String,p08:String,p09:String,p10:String,p11:String,p12:String,p13:String,p14:String,p15:String,p16:String,p17:String,
                                   p18:String,p19:String,p20:String,
                                   p24:String,p25:String,p26:String)=>{

        val coordinateRotationDoubles: Array[Double] = fluxDataCorrection.DRUtil(
          p06.toDouble,p07.toDouble,p08.toDouble,p09.toDouble,p10.toDouble,p11.toDouble,p12.toDouble,p13.toDouble,
          p14.toDouble,p15.toDouble,p16.toDouble,p17.toDouble, p18.toDouble,p19.toDouble,p20.toDouble,
          p24.toDouble,p25.toDouble,p26.toDouble)
        val Fc = coordinateRotationDoubles(0).formatted("%.5f")
        val LE = coordinateRotationDoubles(1).formatted("%.5f")
        val Hs = coordinateRotationDoubles(2).formatted("%.5f")
        val u_star = coordinateRotationDoubles(3).formatted("%.5f")

        Fc+","+LE+","+Hs+","+u_star
      })

      originDF.drop(FcField).drop(LeField).drop(HsField).drop(u_starField).createOrReplaceTempView("DRCoordinateRotation")
      val resultDF = spark.sql(
        s"""
          |select *
          |      ,split(DrUdf(${p06},${p07},${p08},${p09},${p10},${p11},${p12},${p13},${p14},${p15},${p16},${p17},${p18},${p19},${p20},${p24},${p25},${p26}),',')[0] as ${FcField}
          |      ,split(DrUdf(${p06},${p07},${p08},${p09},${p10},${p11},${p12},${p13},${p14},${p15},${p16},${p17},${p18},${p19},${p20},${p24},${p25},${p26}),',')[1] as ${LeField}
          |      ,split(DrUdf(${p06},${p07},${p08},${p09},${p10},${p11},${p12},${p13},${p14},${p15},${p16},${p17},${p18},${p19},${p20},${p24},${p25},${p26}),',')[2] as ${HsField}
          |      ,split(DrUdf(${p06},${p07},${p08},${p09},${p10},${p11},${p12},${p13},${p14},${p15},${p16},${p17},${p18},${p19},${p20},${p24},${p25},${p26}),',')[3] as ${u_starField}
          | from DRCoordinateRotation
          |""".stripMargin)

      resultDF
    }

  /**
   * 平面拟合旋转（PF）
   * @param spark
   * @param originDF
   * @param FcField    Fc         :  CO2通量
   * @param LeField    Le         :  潜热通量
   * @param HsField    Hs         :  显热通量
   * @param u_starField    u_star         :  摩擦风速
   * @param p06        cov_Uz_Uz	:  垂直风速方差
   * @param p07        cov_Uz_Ux	:  垂直风速与X方向风速协方差
   * @param p08        cov_Uz_Uy	:  垂直风速与Y方向风速协方差
   * @param p09        cov_Uz_co2 :  垂直风速与CO2密度协方差
   * @param p10        cov_Uz_h2o :  垂直风速与H2O密度协方差
   * @param p11        cov_Uz_Ts  :  垂直风速与温度协方差
   * @param p12        cov_Ux_Ux	:  X方向风速方差	p12
   * @param p13        cov_Ux_Uy	:  X与Y方向风速协方差
   * @param p14        cov_Ux_co2 :  X方向风速与CO2密度协方差
   * @param p15        cov_Ux_h2o :  X方向风速与H2O密度协方差
   * @param p16        cov_Ux_Ts  :  X方向风速与温度协方差
   * @param p17        cov_Uy_Uy	:  Y方向风速方差
   * @param p18        cov_Uy_co2 :  Y方向风速与CO2密度协方差
   * @param p19        cov_Uy_h2o :  Y方向风速与H2O密度协方差
   * @param p20        cov_Uy_Ts  :  Y方向风速与温度协方差
   * @param p24        Ux_Avg     :  X方向平均风速
   * @param p25        Uy_Avg     :  Y方向平均风速
   * @param p26        Uz_Avg     :  Z方向平均风速
   * @return
   */
  def PFCoordinateRotationUtil(spark:SparkSession,originDF:DataFrame,FcField:String,LeField:String,HsField:String,u_starField:String
                               ,p06:String,p07:String,p08:String,p09:String,p10:String,p11:String,p12:String,p13:String,p14:String,p15:String,p16:String,p17:String,
                               p18:String,p19:String,p20:String,
                               p24:String,p25:String,p26:String
                              ):DataFrame={

    //    平均垂直风速𝑤可以表示为水平风速（𝑢、𝑣）的线性关系函数(p24,p25)
    // 利用最小二乘原理构建方程组，拟合回归求解 b0/b1/b2系数
    val rows: Array[Row] = originDF.select(p24, p25, p26).collect()
    println(rows.size)
    val uvArray = new ArrayBuffer[Array[Double]](rows.size)
    val wArray = ArrayBuffer[Double]()

    rows.foreach(x=>{
      val uvDouble = Array[Double](x(0).toString.toDouble, x(1).toString.toDouble)
      uvArray.+=(uvDouble)
      wArray.+=(x(2).toString.toDouble)
    })

    val doubles: Array[Double] = Theleastsquaremethod.train(wArray.toArray,uvArray.toArray)
    val b0 = doubles(0)
    val b1 = doubles(1)
    val b2 = doubles(2)

    spark.udf.register("PFUdf" ,(p06:String,p07:String,p08:String,p09:String,p10:String,p11:String,p12:String,p13:String,
                                 p14:String,p15:String,p16:String,p17:String, p18:String,p19:String,p20:String)=>{
      val coordinateRotationDoubles: Array[Double] =fluxDataCorrection.PFUtil(
        p06.toDouble,p07.toDouble,p08.toDouble,p09.toDouble,p10.toDouble,p11.toDouble,p12.toDouble,p13.toDouble,
        p14.toDouble,p15.toDouble,p16.toDouble,p17.toDouble, p18.toDouble,p19.toDouble,p20.toDouble,b1,b2)

      val Fc = coordinateRotationDoubles(0).formatted("%.5f")
      val LE = coordinateRotationDoubles(1).formatted("%.5f")
      val Hs = coordinateRotationDoubles(2).formatted("%.5f")
      val u_star = coordinateRotationDoubles(3).formatted("%.5f")

      Fc+","+LE+","+Hs+","+u_star
    })

    originDF.drop(FcField).drop(LeField).drop(HsField).drop(u_starField).createOrReplaceTempView("temp")
    val resultDF = spark.sql(
      s"""
         |select *
         |       ,round(split(PFUdf(${p06},${p07},${p08},${p09},${p10},${p11},${p12},${p13},${p14},${p15},${p16},${p17},${p18},${p19},${p20}),',')[0],5)  as ${FcField}
         |       ,round(split(PFUdf(${p06},${p07},${p08},${p09},${p10},${p11},${p12},${p13},${p14},${p15},${p16},${p17},${p18},${p19},${p20}),',')[0],5)  as ${LeField}
         |       ,round(split(PFUdf(${p06},${p07},${p08},${p09},${p10},${p11},${p12},${p13},${p14},${p15},${p16},${p17},${p18},${p19},${p20}),',')[0],5)  as ${HsField}
         |       ,round(split(PFUdf(${p06},${p07},${p08},${p09},${p10},${p11},${p12},${p13},${p14},${p15},${p16},${p17},${p18},${p19},${p20}),',')[0],5)  as ${u_starField}
         | from temp
         |""".stripMargin)

    resultDF
  }

  /**
   *  WPL 校正
   * @param spark
   * @param originDF
   * @param FcField        Fc         :  CO2通量
   * @param LeField        Le         :  潜热通量
   * @param HsField        Hs         :  显热通量
   * @param p27            co2_Avg    :  平均CO2密度
   * @param p28            h2o_Avg    :  平均H2O密度
   * @param p29            Ts_Avg     :  平均超声空气温度
   * @param p30            rho_a_Avg  :  平均空气密度
   * @return
   */
  def wplCorrectionUtil(spark:SparkSession,originDF:DataFrame,FcField:String,LeField:String,HsField:String,p27:String,p28:String,p29:String,p30:String):DataFrame={

    spark.udf.register("wplUdf" ,(FC:String,LE:String,Hs:String,p27:String,p28:String,p29:String,p30:String)=>{
      
      val wplDouble = fluxDataCorrection.wplUtil(FC.toDouble,LE.toDouble,Hs.toDouble,p27.toDouble,p28.toDouble,p29.toDouble,p30.toDouble)
      val Fc_new = wplDouble(0).formatted("%.5f")
      val Le_new = wplDouble(1).formatted("%.5f")
      val Hs_new = wplDouble(2).formatted("%.5f")
      Fc_new+","+Le_new+","+Hs_new
    })


    val stringBuilder = new StringBuilder
    originDF.schema.fieldNames.foreach(x=>{
      if(x.equals(FcField)) {
        stringBuilder.append(s"split(wplUdf(${FcField},${LeField},${HsField},${p27},${p28},${p29},${p30}),',')[0] as  ${FcField}")
      } else if(x.equals(LeField)){
        stringBuilder.append(s"split(wplUdf(${FcField},${LeField},${HsField},${p27},${p28},${p29},${p30}),',')[1] as  ${LeField}")
      } else if(x.equals(HsField)){
        stringBuilder.append(s"split(wplUdf(${FcField},${LeField},${HsField},${p27},${p28},${p29},${p30}),',')[2] as  ${HsField}")
      } else {
        stringBuilder.append(x)
      }
      stringBuilder.append(",")
    })

    originDF.createOrReplaceTempView("wplCorrectionUtil")
    val resultDF = spark.sql(
      s"""
        | select ${stringBuilder.dropRight(1)} from wplCorrectionUtil
        |""".stripMargin)

    resultDF
  }

  /**
   * 通量储存项计算 涡度法（EC）
   * @param spark
   * @param originDF
   * @param FcField    Fc	CO2通量	p1
   * @param p27        co2_Avg	平均CO2密度	p27
   * @param para_H     通量观测设备观测高度 39.0 米
   * @param flagValue  标识位赋值，不符合条件
   * @return
   */
  def FluxEC_new(spark:SparkSession,originDF:DataFrame,FcField:String, p27: String,para_H: String ,flagValue: String): DataFrame = {

    val para_ht: Double = para_H.toDouble / 1800

    val originIDDF = originDF.repartition(1).orderBy("day_id","hour")
      .withColumn("id",monotonically_increasing_id()).repartition(20)
    originIDDF.createOrReplaceTempView("originIDDF")

    val Lv:Double= 2440
    val Cp :Double= 1.00467*1000

    originIDDF.select("id",p27).createOrReplaceTempView("local_temp")
    val ecDF = spark.sql(
      s"""
        |select a.id
        |   ,Round(if(a.${p27} = ${flagValue} or b.${p27}= ${flagValue} and (a.${p27}-b.${p27})>150,0, (a.${p27}-b.${p27}) * ${para_ht} ) ,5) as ec_fc
        |from local_temp a
        |left join local_temp b on a.id=b.id+1
        |""".stripMargin)
    ecDF.createOrReplaceTempView("ecDF")

    val strSql: StringBuilder = new StringBuilder
    originIDDF.schema.fieldNames.foreach(x=>{
      if(     x.toUpperCase.equals(FcField.toUpperCase))  {
        strSql.append(s"Round(if(ec_fc is not null and ec_fc <> ${flagValue} and ${FcField} <> ${flagValue},${FcField} + ec_fc ,${FcField}),5) as  ${FcField},")
      }
      else {
        strSql.append(s"a.${x} ,")
      }
    })
    val resultDF = spark.sql(
      s"""
        |
        |select  ${strSql.stripSuffix(",")}
        |from originIDDF a
        |left join ecDF b
        |on a.id = b.id
        |
        |""".stripMargin)

    resultDF
  }

  /**
   * 储存项计算 涡度法（EC）
   * @param spark
   * @param originDF
   * @param FcField    Fc	CO2通量	p1
   * @param LeField    LE	潜热通量	p2
   * @param HsField    Hs	显热通量	p3
   * @param p27        co2_Avg	平均CO2密度	p27
   * @param p28        h2o_Avg	平均H2O密度	p28
   * @param p29        Ts_Avg	平均超声空气温度	p29
   * @param para_H     通量观测设备观测高度 39.0 米
   * @param flagValue  标识位赋值，不符合条件
   * @return
   */
//  def FluxEC_new_bak(spark:SparkSession,originDF:DataFrame,FcField:String,LeField:String,HsField:String, p27: String,p28: String,p29: String,p30: String,para_H: String ,flagValue: String): DataFrame = {
//
//    val para_ht: Double = para_H.toDouble / 1800
//
//    val originIDDF = originDF.repartition(1).orderBy("day_id","hour")
//      .withColumn("id",monotonically_increasing_id()).repartition(20)
//    originIDDF.createOrReplaceTempView("originIDDF")
//
//    val Lv:Double= 2440
//    val Cp :Double= 1.00467*1000
//    //    val pa:Double = p30.toDouble * 1000 * 1000
//
//    //    val builder: StringBuilder = new StringBuilder
//    //    originIDDF.schema.fieldNames.foreach(x=>{
//    //      if(x.toUpperCase.equals(FcField.toUpperCase)) {
//    //        builder.append(s"Round( if(a.${p27}<>${flagValue.toDouble}  and b.${p27}<>${flagValue.toDouble} and b.${p27} is not null, (b.${p27}-a.${p27}) * ${para_ht} , ${FcField}) ,5) as  ${FcField},")
//    //
//    //      } else if(x.toUpperCase.equals(FcField.toUpperCase)) {
//    //        builder.append(s"Round( if(a.${p28}<>${flagValue.toDouble}  and b.${p28}<>${flagValue.toDouble} and b.${p28} is not null, (b.${p28}-a.${p28}) * ${para_ht} * ${Lv} , ${LeField}) ,5) as  ${LeField},")
//    //
//    //      } else if(x.toUpperCase.equals(FcField.toUpperCase)) {
//    //        builder.append(s"Round( if(a.${p29}<>${flagValue.toDouble}  and b.${p29}<>${flagValue.toDouble} and b.${p29} is not null, (b.${p29}-a.${p29}) * ${para_ht} * ${Cp} * ${p30} * 1000 * 1000      + ${HsField}, ${HsField}) ,5) as  ${HsField},")
//    //
//    //      } else {
//    //        builder.append(s"a.${x} ,")
//    //      }
//    //    })
//
//    originIDDF.select("id",p27,p28,p29,p30).createOrReplaceTempView("local_temp")
//    val ecDF = spark.sql(
//      s"""
//         |select a.id
//         |   ,Round(if(a.${p27} = ${flagValue} or b.${p27}= ${flagValue} and (a.${p27}-b.${p27})>150,0, (a.${p27}-b.${p27}) * ${para_ht} ) ,5) as ec_fc
//         |   ,Round(if(a.${p28} = ${flagValue} or b.${p28}= ${flagValue} and (a.${p28}-b.${p28})>150,0, (a.${p28}-b.${p28}) * ${para_ht} * ${Lv}) ,5)  as ec_le
//         |   ,Round(if(a.${p29} = ${flagValue} or b.${p29}= ${flagValue} and (a.${p29}-b.${p29})>150,0, (a.${p29}-b.${p29}) * ${para_ht} * ${Cp} * a.${p30} * 1000 * 1000) ,5) as  ec_hs
//         |from local_temp a
//         |left join local_temp b on a.id=b.id+1
//         |""".stripMargin)
//    ecDF.createOrReplaceTempView("ecDF")
//
//
//    val strSql: StringBuilder = new StringBuilder
//    originIDDF.schema.fieldNames.foreach(x=>{
//      if(     x.toUpperCase.equals(FcField.toUpperCase))  strSql.append(s"Round(if(ec_fc is not null and ec_fc <> ${flagValue} and ${FcField} <> ${flagValue},${FcField} + ec_fc ,${FcField}),5) as  ${FcField},")
//      else if(x.toUpperCase.equals(LeField.toUpperCase))  strSql.append(s"Round(if(ec_le is not null and ec_le <> ${flagValue} and ${LeField} <> ${flagValue},${LeField} + ec_le ,${LeField}),5) as  ${LeField},")
//      else if(x.toUpperCase.equals(HsField.toUpperCase))  strSql.append(s"Round(if(ec_hs is not null and ec_hs <> ${flagValue} and ${HsField} <> ${flagValue},${HsField} + ec_hs ,${HsField}),5) as  ${HsField},")
//      else strSql.append(s"a.${x} ,")
//    })
//
//    val resultDF = spark.sql(
//      s"""
//         |
//         |select  ${strSql.stripSuffix(",")}
//         |from originIDDF a
//         |left join ecDF b
//         |on a.id = b.id
//         |
//         |""".stripMargin)
//
//    resultDF
//  }


}
