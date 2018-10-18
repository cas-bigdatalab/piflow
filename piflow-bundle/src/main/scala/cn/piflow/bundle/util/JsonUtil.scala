package cn.piflow.bundle.util

import org.apache.spark.sql.functions.explode
import org.apache.spark.sql.{Column, DataFrame, SQLContext, SparkSession}

import scala.collection.mutable.ArrayBuffer

object JsonUtil extends Serializable{


//  The tag you want to parse,If you want to open an array field,you have to write it like this:links_name(MasterField_ChildField)
  def ParserJsonDF(df:DataFrame,tag:String): DataFrame = {

    var openArrField:String=""
    var ArrSchame:String=""

    var tagARR: Array[String] = tag.split(",")
    var tagNew:String=""


    for(tt<-tagARR){

      if(tt.indexOf("_")> -1){
        //包含“.”
        val openField: Array[String] = tt.split("_")
        openArrField=openField(0)

        ArrSchame+=(openField(1)+",")
      }else{
        tagNew+=(tt+",")
      }
    }
    tagNew+=openArrField
    ArrSchame=ArrSchame.substring(0,ArrSchame.length-1)

    tagARR = tagNew.split(",")
    var FinalDF:DataFrame=df

    //如果用户选择返回字段
    var strings: Seq[Column] =tagNew.split(",").toSeq.map(p => new Column(p))

    if(tag.length>0){
      val df00 = FinalDF.select(strings : _*)
      FinalDF=df00
    }

    //如果用户选择打开的数组字段，并给出schame
    if(openArrField.length>0&&ArrSchame.length>0){

      val schames: Array[String] = ArrSchame.split(",")

      var selARR:ArrayBuffer[String]=ArrayBuffer()//分别取出已经打开的字段
      //遍历数组，封装到column对象中
      var coARR:ArrayBuffer[Column]=ArrayBuffer()//打开字段的select方法用
      val sss = tagNew.split(",")//打开字段后todf方法用
      var co: Column =null
      for(each<-tagARR){
        if(each==openArrField){
          co = explode(FinalDF(openArrField))
          for(x<-schames){

            selARR+=(openArrField+"."+x)
          }
        }else{
          selARR+=each
          co=FinalDF(each)
        }
        coARR+=co
      }
      println("###################")
      selARR.foreach(println(_))
      var selSEQ: Seq[Column] = selARR.toSeq.map(q => new Column(q))

      var df01: DataFrame = FinalDF.select(coARR : _*).toDF(sss:_*)
      FinalDF = df01.select(selSEQ : _*)

    }

FinalDF

  }
}
