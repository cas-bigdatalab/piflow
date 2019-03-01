package cn.piflow.api

import org.apache.http.client.methods.{CloseableHttpResponse, HttpPost}
import org.apache.http.entity.StringEntity
import org.apache.http.impl.client.HttpClients
import org.apache.http.util.EntityUtils

object HTTPClientStartFlowStreaming {

  def main(args: Array[String]): Unit = {
    /*val json =
      """
        |{
        |  "flow":{
        |    "name":"kafkaStreaming",
        |    "uuid":"1234",
        |    "stops":[
        |      {
        |        "uuid":"1111",
        |        "name":"kafkaStream",
        |        "bundle":"cn.piflow.bundle.streaming.KafkaStream",
        |        "properties":{
        |          "brokers":"10.0.86.191:9092,10.0.86.203:9092,10.0.86.210:9092",
        |          "groupId":"piflow",
        |          "topics":"streaming"
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
        |        "from":"kafkaStream",
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
      """.stripMargin*/
    /*val json=
      """
        |{
        |  "flow":{
        |    "name":"flumeStreaming",
        |    "uuid":"1234",
        |    "stops":[
        |      {
        |        "uuid":"1111",
        |        "name":"SocketTextStream",
        |        "bundle":"cn.piflow.bundle.streaming.FlumeStream",
        |        "properties":{
        |            "hostname":"10.0.86.210",
        |            "port":"7777"
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
        |        "from":"SocketTextStream",
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
      """.stripMargin*/
    val json =
      """
        |{
        |  "flow":{
        |    "name":"TextFileStream",
        |    "uuid":"1234",
        |    "stops":[
        |      {
        |        "uuid":"1111",
        |        "name":"TextFileStream",
        |        "bundle":"cn.piflow.bundle.streaming.TextFileStream",
        |        "properties":{
        |            "directory":"hdfs://10.0.86.89:9000/textfilestream"
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
        |        "from":"TextFileStream",
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
