package cn.piflow.bundle.packone

import cn.piflow.bundle.util.XmlToJson
import com.alibaba.fastjson.JSON
import org.apache.spark.rdd.RDD
import org.apache.spark.sql.{DataFrame, SparkSession}

object test {

  val spark = SparkSession.builder()
    .master("local[12]")
    .appName("packone_139")
    .config("spark.deploy.mode","client")
    .config("spark.driver.memory", "15g")
    .config("spark.executor.memory", "32g")
    .config("spark.cores.max", "16")
    .config("hive.metastore.uris","thrift://192.168.3.140:9083")
    .enableHiveSupport()
    .getOrCreate()

  def main(args: Array[String]): Unit = {



    fund_new()

  }

  def fund_new()={
    val xmlColumns = "PRODUCT_XML"

    spark.sqlContext.udf.register("xml_n",(str:String)=>{
      str.replaceAll("\n","   ")
    })


    val df = spark.sql("select * from origin_piflow.o_product_person_ext  limit 100 ")
    df.createOrReplaceTempView("df")
    df.show(1)




    spark.sqlContext.udf.register("xmlToJson",(str:String)=>{
      XmlToJson.xmlParse(str.replaceAll("\n","  "))
    })
    val columns: Array[String] = xmlColumns.toLowerCase.split(",")



    val fields: Array[String] = df.schema.fieldNames
    var fieldString = new StringBuilder
    fields.foreach(x=>{
      if (columns.contains(x.toLowerCase)){
        fieldString.append(s"xmlToJson(${x}) as ${x} ,")
      } else {
        fieldString.append(s"${x},")
      }
    })

    println(fieldString)

    df.createOrReplaceTempView("temp")
    val sqlText = "select " +fieldString.stripSuffix(",")+ " from temp"

    println(sqlText)
    val frame: DataFrame = spark.sql(sqlText)
    frame.show(1)

    val str = "   [{\n            \"is_mine\":\"否\",\n            \"is_message\":0,\n            \"first_author\":0,\n            \"psn_name\":\"金连文\",\n            \"org_name\":\"\",\n            \"email\":\"\"\n        },\n        {\n            \"is_mine\":\"否\",\n            \"is_message\":0,\n            \"first_author\":0,\n            \"psn_name\":\"邓国强\",\n            \"org_name\":\"\",\n            \"email\":\"\"\n        }]"

    val aa = str.replace("\n", "").replace("}\"", "}").replace(":\"{", ":{").replace("\\","")
        .replace(" ","")
    println(aa)

    val bb = "{\n            \"is_mine\":\"否\",\n            \"is_message\":0,\n            \"first_author\":0,\n            \"psn_name\":\"金连文\",\n            \"org_name\":\"\",\n            \"email\":\"\"\n        }"

   println( parseAuthor_piflow(bb))



  }



  def parseAuthor_piflow(str :String):String={

    val psn_name= new StringBuilder
    val org_name= new StringBuilder
    val email= new StringBuilder
    val is_message= new StringBuilder
    val firsr_author= new StringBuilder
    val is_mine= new StringBuilder

    if (str == null){
      psn_name.append("null"+"#")
      org_name.append("null"+"#")
      email.append("null"+"#")
      is_message.append("null"+"#")
      firsr_author.append("null"+"#")
      is_mine.append("null"+"#")
    }
    else if (str.replace(" ","").startsWith("[{")){
      val jsonArray = JSON.parseArray(str)
      if(jsonArray.size>0) {
        for (i <- 0 until jsonArray.size()) {
          if(jsonArray.get(i).toString.contains("psn_name")){
            val jSONObject = jsonArray.getJSONObject(i)

            psn_name.append(jSONObject.get("psn_name") + "#")
            org_name.append(jSONObject.get("org_name") + "#")
            email.append(jSONObject.get("email") + "#")
            is_message.append(jSONObject.get("is_message") + "#")
            firsr_author.append(jSONObject.get("first_author") + "#")
            is_mine.append(jSONObject.get("is_mine") + "#")
            jSONObject.clear()

          } else {
            psn_name.append("null"+"#")
            org_name.append("null"+"#")
            email.append("null"+"#")
            is_message.append("null"+"#")
            firsr_author.append("null"+"#")
            is_mine.append("null"+"#")
          }
        }
      } else {
        psn_name.append("null"+"#")
        org_name.append("null"+"#")
        email.append("null"+"#")
        is_message.append("null"+"#")
        firsr_author.append("null"+"#")
        is_mine.append("null"+"#")
      }
    } else if (str.replace(" ","").startsWith("{")){
      println(str)
      val jSONObject = JSON.parseObject(str)
      psn_name.append(jSONObject.get("psn_name")+"#")
      org_name.append(jSONObject.get("org_name")+"#")
      email.append(jSONObject.get("email")+"#")
      is_message.append(jSONObject.get("is_message")+"#")
      firsr_author.append(jSONObject.get("first_author")+"#")
      is_mine.append(jSONObject.get("is_mine")+"#")
      jSONObject.clear()
    }
    else {
      psn_name.append("null"+"#")
      org_name.append("null"+"#")
      email.append("null"+"#")
      is_message.append("null"+"#")
      firsr_author.append("null"+"#")
      is_mine.append("null"+"#")
    }

    psn_name.toString().stripSuffix("#") + "≌"+
      org_name.toString().stripSuffix("#")+ "≌"+
      email.toString().stripSuffix("#")+ "≌"+
      is_message.toString().stripSuffix("#")+ "≌"+
      firsr_author.toString().stripSuffix("#")+ "≌"+
      is_mine.toString().stripSuffix("#")

  }
















}
