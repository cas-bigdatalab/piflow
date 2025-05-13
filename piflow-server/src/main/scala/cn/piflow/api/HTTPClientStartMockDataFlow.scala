package cn.piflow.api

import org.apache.http.client.config.RequestConfig
import org.apache.http.client.methods.{CloseableHttpResponse, HttpPost}
import org.apache.http.entity.StringEntity
import org.apache.http.impl.client.HttpClientBuilder
import org.apache.http.util.EntityUtils

object HTTPClientStartMockDataFlow {

  def main(args: Array[String]): Unit = {

    val json =
      """
        |{
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
      """.stripMargin
    val json_2 =
      """
        |{
        |    "flow": {
        |        "name": "Example",
        |        "executorMemory": "1g",
        |        "executorNumber": "1",
        |        "uuid": "8a80d63f720cdd2301723a4e679e2457",
        |        "paths": [
        |            {
        |                "inport": "",
        |                "from": "CsvParser",
        |                "to": "CsvSave",
        |                "outport": ""
        |            }
        |        ],
        |        "executorCores": "1",
        |        "driverMemory": "1g",
        |        "stops": [
        |            {
        |                "name": "CsvSave",
        |                "bundle": "cn.piflow.bundle.csv.CsvSave",
        |                "uuid": "8a80d63f720cdd2301723a4e67a52467",
        |                "properties": {
        |                    "csvSavePath": "hdfs://172.18.39.41:9000/user/Yomi/test1.csv",
        |                    "partition": "",
        |                    "header": "false",
        |                    "saveMode": "append",
        |                    "delimiter": ","
        |                },
        |                "customizedProperties": {
        |
        |                }
        |            },
        |            {
        |                "name": "CsvParser",
        |                "bundle": "cn.piflow.bundle.csv.CsvParser",
        |                "uuid": "8a80d63f720cdd2301723a4e67a82470",
        |                "properties": {
        |                    "schema": "title,author,pages",
        |                    "csvPath": "hdfs://172.18.39.41:9000/user/Yomi/test.csv",
        |                    "delimiter": ",",
        |                    "header": "false"
        |                },
        |                "customizedProperties": {
        |
        |                }
        |            }
        |        ]
        |    }
        |}
        |
        |""".stripMargin
    val json3=
      """
        |{
        |    "flow": {
        |        "name": "Example",
        |        "executorMemory": "1g",
        |        "executorNumber": "1",
        |        "uuid": "8a80d63f720cdd2301723a4e679e2457",
        |        "paths": [
        |            {
        |                "inport": "",
        |                "from": "CsvParser",
        |                "to": "ArrowFlightOut",
        |                "outport": ""
        |            }
        |        ],
        |        "executorCores": "1",
        |        "driverMemory": "1g",
        |        "stops": [
        |            {
        |                "name": "ArrowFlightOut",
        |                "bundle": "cn.piflow.bundle.arrowflight.ArrowFlightOut",
        |                "uuid": "8a80d63f720cdd2301723a4e67a52467",
        |                "properties": {
        |                    "outputIp": "127.0.0.1",
        |                },
        |                "customizedProperties": {
        |
        |                }
        |            },
        |            {
        |                "name": "CsvParser",
        |                "bundle": "cn.piflow.bundle.csv.CsvParser",
        |                "uuid": "8a80d63f720cdd2301723a4e67a82470",
        |                "properties": {
        |                    "schema": "title,author,pages",
        |                    "csvPath": "hdfs://172.18.39.41:9000/user/Yomi/test.csv",
        |                    "delimiter": ",",
        |                    "header": "false"
        |                },
        |                "customizedProperties": {
        |
        |                }
        |            }
        |        ]
        |    }
        |}
        |
        |""".stripMargin
    val url = "http://172.18.32.1:8002/flow/start"
    val timeout = 1800
    val requestConfig = RequestConfig.custom()
      .setConnectTimeout(timeout*1000)
      .setConnectionRequestTimeout(timeout*1000)
      .setSocketTimeout(timeout*1000).build()

    val client = HttpClientBuilder.create().setDefaultRequestConfig(requestConfig).build()

    val post:HttpPost = new HttpPost(url)
    post.addHeader("Content-Type", "application/json")
    post.setEntity(new StringEntity(json3))


    val response:CloseableHttpResponse = client.execute(post)
    val entity = response.getEntity
    val str = EntityUtils.toString(entity,"UTF-8")
    println("Code is " + str)
  }

}
