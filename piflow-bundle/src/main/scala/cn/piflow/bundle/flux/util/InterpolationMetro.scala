package cn.piflow.bundle.flux.util

import cn.piflow.bundle.flux.util.CommonUtil.toTimeStamp
import org.apache.spark.sql.functions.{col, lit, udf}
import org.apache.spark.sql.{DataFrame, SparkSession}

/**
 * @Author renhao
 * @Description:
 * @Data 2023/3/28 13:35
 * @Modified By:
 */
class InterpolationMetro extends Serializable {


  def runin(d1:Double,d2:Double,d3:Double,d4:Double,d5:Double,flagValue:Integer): Double ={

    if(d1==null || d5==null){
      println("-----------------------------------------------------------------------------------------------------")
      println(d1,d2,d3,d4,d5)
    }
    if(d2==flagValue&&d3==flagValue&&d4!=flagValue&&d1!=null&&d1.toString.toDouble!=flagValue){
//      (d1.toString.toDouble+d4)/2
      d1.toString.toDouble+math.abs(d1.toString.toDouble-d4)*2/3
    }else if(d3==flagValue&&d4==flagValue&&d2!=flagValue&&d5!=null&&d5.toString.toDouble!=flagValue){
//      (d2+d5.toString.toDouble)/2
      d2+math.abs(d2-d5.toString.toDouble)/3
    }else{
      d3
    }
  }
  def filterFile(d:String,flagValue:Integer): Double ={
    if(d==null){
      flagValue.toDouble
    }else{
      d.toDouble
    }
  }

  def imputationReplacement(spark:SparkSession,df:DataFrame,arrayFiled:String,time_nterval:Integer,flagVaue:Integer): DataFrame ={
    import spark.implicits._
    val toTime = udf(toTimeStamp _)
    val df1 = df.withColumn("timeStamp",toTime(col("year"),col("month"),col("day"),col("hour")))

    val df2 = df1.as("c").join(df1.as("a"),$"c.timeStamp"===$"a.timeStamp".plus(time_nterval*1000*2),"left")
      .join(df1.as("b"),$"c.timeStamp"===$"b.timeStamp".plus(time_nterval*1000),"left")
      .join(df1.as("d"),$"c.timeStamp"===$"d.timeStamp".minus(time_nterval*1000),"left")
      .join(df1.as("e"),$"c.timeStamp"===$"e.timeStamp".minus(time_nterval*1000*2),"left")
      .where(s"b.${arrayFiled.split(",")(0)} is not null and d.${arrayFiled.split(",")(0)} is not null")

//    df2.orderBy($"c.timeStamp").select($"c.timeStamp",$"c.year",$"c.month",$"c.day",$"c.hour",$"c.Ta_1_AVG"
//      ,$"a.Ta_1_AVG",$"b.Ta_1_AVG",$"d.Ta_1_AVG",$"e.Ta_1_AVG").show(50)
    //a b c d e
    val caculate = udf(runin _)
    val f = udf(filterFile _)
    val df3 = df2.select(arrayFiled.split(",")
      .map(x=>caculate(f($"a.$x",lit(flagVaue)),f($"b.$x",lit(flagVaue)),f($"c.$x",lit(flagVaue)),f($"d.$x",lit(flagVaue)),f($"e.$x",lit(flagVaue)),lit(flagVaue)).as(x)).++(Array(col("c.timeStamp"))): _*)
    val resultCol = df.schema.map(_.name)
    val resultDF = df1.as("a").join(df3.as("b"),Seq("timeStamp"),"left")
    resultDF.where(s"b.${arrayFiled.split(",")(0)} is not null")
      .select(resultCol.map(x=>{
        if(arrayFiled.split(",").contains(x)){
          col(s"b.$x")
        }else{
          col(x)
        }
      }): _*)
      .union(resultDF.where(s"b.${arrayFiled.split(",")(0)} is null").select(resultCol.map(x=>col(s"a.$x")): _*))
  }
}
