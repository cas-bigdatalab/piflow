package cn.piflow.api

import org.apache.http.client.methods.{CloseableHttpResponse, HttpPost}
import org.apache.http.entity.StringEntity
import org.apache.http.impl.client.HttpClients
import org.apache.http.util.EntityUtils

object HTTPClientStartFlow1 {

  def main(args: Array[String]): Unit = {
    val json =
      """
        |{
        |  "flow":{
        |    "name":"test",
        |    "uuid":"1234",
        |    "checkpoint":"Merge",
        |    "stops":[
        |      {
        |        "uuid":"1111",
        |        "name":"XmlParser",
        |        "bundle":"cn.piflow.bundle.xml.XmlParser",
        |        "properties":{
        |            "xmlpath":"hdfs://10.0.86.89:9000/xjzhu/dblp.mini.xml",
        |            "rowTag":"phdthesis"
        |        }
        |
        |      },
        |      {
        |        "uuid":"2222",
        |        "name":"SelectField",
        |        "bundle":"cn.piflow.bundle.common.SelectField",
        |        "properties":{
        |            "schema":"title,author,pages"
        |        }
        |
        |      },
        |      {
        |        "uuid":"888",
        |        "name":"CsvSave",
        |        "bundle":"cn.piflow.bundle.csv.CsvSave",
        |        "properties":{
        |          "csvSavePath":"hdfs://10.0.86.89:9000/xjzhu/phdthesis_result.csv",
        |          "header":"true",
        |          "delimiter":","
        |        }
        |      }
        |    ],
        |    "paths":[
        |      {
        |        "from":"XmlParser",
        |        "outport":"",
        |        "inport":"",
        |        "to":"SelectField"
        |      },
        |      {
        |        "from":"SelectField",
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
