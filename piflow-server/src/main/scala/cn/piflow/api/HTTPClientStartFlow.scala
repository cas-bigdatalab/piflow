package cn.piflow.api

import org.apache.http.client.config.RequestConfig
import org.apache.http.client.methods.{CloseableHttpResponse, HttpGet, HttpPost}
import org.apache.http.entity.StringEntity
import org.apache.http.impl.client.{HttpClientBuilder, HttpClients}
import org.apache.http.util.EntityUtils

object HTTPClientStartFlow {

  def main(args: Array[String]): Unit = {

    val json =
      """
        |{
        |  "flow": {
        |    "name": "Flink-1",
        |    "executorMemory": "1g",
        |    "executorNumber": "1",
        |    "executorCores": "1",
        |    "driverMemory": "1g",
        |    "uuid": "8a80d63f720cdd2301723b7461d92600",
        |    "paths": [
        |      {
        |        "inport": "",
        |        "from": "SensorSourceStop",
        |        "to": "AverageTemperature",
        |        "outport": ""
        |      }
        |    ],

        |    "stops": [
        |      {
        |        "name": "SensorSourceStop",
        |        "bundle": "cn.piflow.bundle.stream.SensorSourceStop",
        |        "uuid": "8a80d63f720cdd2301723b7461d92604",
        |        "properties": {
        |
        |        },
        |        "customizedProperties": {
        |
        |        }
        |      },
        |      {
        |        "name": "AverageTemperature",
        |        "bundle": "cn.piflow.bundle.stream.AverageTemperature",
        |        "uuid": "8a80d63f720cdd2301723b7461d92602",
        |        "properties": {
        |
        |        },
        |        "customizedProperties": {
        |
        |        }
        |      }
        |    ]
        |  }
        |}
        |
      """.stripMargin


    val url = "http://223.193.3.32:8001/flink/flow/start"
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
