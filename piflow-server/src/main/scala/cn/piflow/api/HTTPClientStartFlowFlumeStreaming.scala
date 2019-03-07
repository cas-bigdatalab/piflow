package cn.piflow.api

import org.apache.http.client.methods.{CloseableHttpResponse, HttpPost}
import org.apache.http.entity.StringEntity
import org.apache.http.impl.client.HttpClients
import org.apache.http.util.EntityUtils

object HTTPClientStartFlowFlumeStreaming {

  def main(args: Array[String]): Unit = {
    //flume hostname must be one of the cluster worker node, the port should be greater than 10000
    val json=
      """
        |{
        |  "flow":{
        |    "name":"flumeStreaming",
        |    "uuid":"1234",
        |    "stops":[
        |      {
        |        "uuid":"1111",
        |        "name":"FlumeStream",
        |        "bundle":"cn.piflow.bundle.streaming.FlumeStream",
        |        "properties":{
        |            "hostname":"slave2",
        |            "port":"10002",
        |            "batchDuration":"5"
        |        }
        |
        |      },
        |      {
        |        "uuid":"2222",
        |        "name":"ConvertSchema",
        |        "bundle":"cn.piflow.bundle.common.ConvertSchema",
        |        "properties":{
        |          "schema":"value->line"
        |        }
        |      },
        |      {
        |        "uuid":"3333",
        |        "name":"CsvSave",
        |        "bundle":"cn.piflow.bundle.csv.CsvSave",
        |        "properties":{
        |          "csvSavePath":"hdfs://10.0.86.89:9000/xjzhu/flowStreaming",
        |          "header":"true",
        |          "delimiter":","
        |        }
        |      }
        |    ],
        |    "paths":[
        |      {
        |        "from":"FlumeStream",
        |        "outport":"",
        |        "inport":"",
        |        "to":"ConvertSchema"
        |      },
        |      {
        |        "from":"ConvertSchema",
        |        "outport":"",
        |        "inport":"",
        |        "to":"CsvSave"
        |      }
        |    ]
        |  }
        |}
      """.stripMargin

    val url = "http://10.0.86.98:8001/flow/start"
    val client = HttpClients.createDefault()
    val post:HttpPost = new HttpPost(url)

    post.addHeader("Content-Type", "application/json")
    post.setEntity(new StringEntity(json))


    val response:CloseableHttpResponse = client.execute(post)
    val entity = response.getEntity
    val str = EntityUtils.toString(entity,"UTF-8")
    println("Code is " + str)
  }

}
