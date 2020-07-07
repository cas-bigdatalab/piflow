package cn.piflow.api

import org.apache.http.client.config.RequestConfig
import org.apache.http.client.methods.{CloseableHttpResponse, HttpPost}
import org.apache.http.entity.StringEntity
import org.apache.http.impl.client.HttpClientBuilder
import org.apache.http.util.EntityUtils

object HTTPClientScheduleFlow {

  def main(args: Array[String]): Unit = {
    val json =
      """
        |{
        |	"expression": "0 0/5 * * * ? *",
        | "startDate" : "2020-07-07 12:00:00",
        | "endData" : "",
        |	"schedule":{
        |  "flow": {
        |    "name": "MockData",
        |    "executorMemory": "1g",
        |    "executorNumber": "1",
        |    "uuid": "8a80d63f720cdd2301723b7461d92600",
        |    "paths": [
        |      {
        |        "inport": "",
        |        "from": "MockData",
        |        "to": "ShowData",
        |        "outport": ""
        |      }
        |    ],
        |    "executorCores": "1",
        |    "driverMemory": "1g",
        |    "stops": [
        |      {
        |        "name": "MockData",
        |        "bundle": "cn.piflow.bundle.common.MockData",
        |        "uuid": "8a80d63f720cdd2301723b7461d92604",
        |        "properties": {
        |          "schema": "title:String, author:String, age:Int",
        |          "count": "10"
        |        },
        |        "customizedProperties": {
        |
        |        }
        |      },
        |      {
        |        "name": "ShowData",
        |        "bundle": "cn.piflow.bundle.external.ShowData",
        |        "uuid": "8a80d63f720cdd2301723b7461d92602",
        |        "properties": {
        |          "showNumber": "5"
        |        },
        |        "customizedProperties": {
        |
        |        }
        |      }
        |    ]
        |  }
        |}
        |
        |}
      """.stripMargin
    val url = "http://10.0.85.83:8001/schedule/start"
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
