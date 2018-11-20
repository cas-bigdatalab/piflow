package cn.piflow.api

import org.apache.http.client.methods.{CloseableHttpResponse, HttpPost}
import org.apache.http.entity.StringEntity
import org.apache.http.impl.client.HttpClients
import org.apache.http.util.EntityUtils

object HTTPClientStartFlowByCheckPoint {

  def main(args: Array[String]): Unit = {
    val json ="""
                |{
                |  "flow":{
                |    "name":"xml,csv-merge-fork-hive,json,csv",
                |    "uuid":"1234",
                |    "checkpoint":"Merge",
                |    "checkpointParentProcessId":"process_67adfebe-1792-4baa-abc0-1591d29e0d49_1",
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
                |        "uuid":"3333",
                |        "name":"PutHiveStreaming",
                |        "bundle":"cn.piflow.bundle.hive.PutHiveStreaming",
                |        "properties":{
                |            "database":"sparktest",
                |            "table":"dblp_phdthesis"
                |        }
                |      },
                |      {
                |        "uuid":"4444",
                |        "name":"CsvParser",
                |        "bundle":"cn.piflow.bundle.csv.CsvParser",
                |        "properties":{
                |            "csvPath":"hdfs://10.0.86.89:9000/xjzhu/phdthesis.csv",
                |            "header":"false",
                |            "delimiter":",",
                |            "schema":"title,author,pages"
                |        }
                |      },
                |      {
                |        "uuid":"555",
                |        "name":"Merge",
                |        "bundle":"cn.piflow.bundle.common.Merge",
                |        "properties":{
                |          "inports":"data1,data2"
                |        }
                |      },
                |      {
                |        "uuid":"666",
                |        "name":"Fork",
                |        "bundle":"cn.piflow.bundle.common.Fork",
                |        "properties":{
                |          "outports":"out1,out2,out3"
                |        }
                |      },
                |      {
                |        "uuid":"777",
                |        "name":"JsonSave",
                |        "bundle":"cn.piflow.bundle.json.JsonSave",
                |        "properties":{
                |          "jsonSavePath":"hdfs://10.0.86.89:9000/xjzhu/phdthesis.json"
                |        }
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
                |        "inport":"data1",
                |        "to":"Merge"
                |      },
                |      {
                |        "from":"CsvParser",
                |        "outport":"",
                |        "inport":"data2",
                |        "to":"Merge"
                |      },
                |      {
                |        "from":"Merge",
                |        "outport":"",
                |        "inport":"",
                |        "to":"Fork"
                |      },
                |      {
                |        "from":"Fork",
                |        "outport":"out1",
                |        "inport":"",
                |        "to":"PutHiveStreaming"
                |      },
                |      {
                |        "from":"Fork",
                |        "outport":"out2",
                |        "inport":"",
                |        "to":"JsonSave"
                |      },
                |      {
                |        "from":"Fork",
                |        "outport":"out3",
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
