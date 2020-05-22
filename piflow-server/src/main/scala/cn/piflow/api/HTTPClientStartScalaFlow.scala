package cn.piflow.api

import org.apache.http.client.config.RequestConfig
import org.apache.http.client.methods.{CloseableHttpResponse, HttpPost}
import org.apache.http.entity.StringEntity
import org.apache.http.impl.client.HttpClientBuilder
import org.apache.http.util.EntityUtils


object HTTPClientStartScalaFlow {

  def main(args: Array[String]): Unit = {


    val json =
      """
        |{
        |  "flow":{
        |    "name":"scalaTest",
        |    "uuid":"1234567890",
        |    "stops":[
        |      {
        |        "uuid":"1111",
        |        "name":"CsvParser",
        |        "bundle":"cn.piflow.bundle.csv.CsvParser",
        |        "properties":{
        |          "csvPath":"hdfs://10.0.86.191:9000/xjzhu/test.csv",
        |          "header":"false",
        |          "delimiter":",",
        |          "schema":"title,author"
        |        }
        |      },
        |      {
        |        "uuid":"2222",
        |        "name":"ExecuteScalaFile",
        |        "bundle":"cn.piflow.bundle.script.ExecuteScalaFile",
        |        "properties":{
        |            "plugin":"stop_scalaTest_ExecuteScalaFile_4444",
        |            "script":"val df = in.read() \n df.createOrReplaceTempView(\"people\") \n val df1 = spark.sql(\"select * from prople where author like 'xjzhu'\") \n out.write(df1);"
        |        }
        |      },
        |      {
        |        "uuid":"3333",
        |        "name":"CsvSave",
        |        "bundle":"cn.piflow.bundle.csv.CsvSave",
        |        "properties":{
        |          "csvSavePath":"hdfs://10.0.86.191:9000/xjzhu/CSVOverwrite",
        |          "header": "true",
        |          "delimiter":",",
        |          "partition":"1",
        |          "saveMode": "overwrite"
        |        }
        |
        |      }
        |    ],
        |    "paths":[
        |      {
        |        "from":"CsvParser",
        |        "outport":"",
        |        "inport":"",
        |        "to":"ExecuteScalaFile"
        |      },
        |      {
        |        "from":"ExecuteScalaFile",
        |        "outport":"",
        |        "inport":"",
        |        "to":"CsvSave"
        |      }
        |    ]
        |  }
        |}
      """.stripMargin



    val url = "http://10.0.85.83:8001/flow/start"
    val timeout = 1800
    val requestConfig = RequestConfig.custom()
      .setConnectTimeout(timeout*1000)
      .setConnectionRequestTimeout(timeout*1000)
      .setSocketTimeout(timeout*1000).build()

    val client = HttpClientBuilder.create().setDefaultRequestConfig(requestConfig).build()

    val post:HttpPost = new HttpPost(url)
    post.addHeader("Content-Type", "application/json")
    post.setEntity(new StringEntity(json))


    val response:CloseableHttpResponse = client.execute(post)
    val entity = response.getEntity
    val str = EntityUtils.toString(entity,"UTF-8")
    println("Code is " + str)
  }

}
