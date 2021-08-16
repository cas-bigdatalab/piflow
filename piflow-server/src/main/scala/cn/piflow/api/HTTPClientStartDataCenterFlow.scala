package cn.piflow.api

import org.apache.http.client.config.RequestConfig
import org.apache.http.client.methods.{CloseableHttpResponse, HttpPost}
import org.apache.http.entity.StringEntity
import org.apache.http.impl.client.HttpClientBuilder
import org.apache.http.util.EntityUtils

object HTTPClientStartDataCenterFlow {

  def main(args: Array[String]): Unit = {

    /*val json =
      """
        |{
        |   "flow": {
        |					"name": "flow1",
        |					"executorMemory": "1g",
        |					"executorNumber": "1",
        |					"uuid": "8a80d63f720cdd2301723b7461d92600",
        |					"executorCores": "1",
        |					"driverMemory": "1g",
        |					"environmentVariable": {
        |						"${SPARK_HOME}": "/opt/data/spark/bin",
        |						"${CODE}": "A00101"
        |					},
        |					"stops": [
        |						{
        |							"dataCenter" : "http://10.0.90.119:8001",
        |							"name": "MockData-A",
        |							"bundle": "cn.piflow.bundle.common.MockData",
        |							"uuid": "8a80d63f720cdd2301723b7461d92604",
        |							"properties": {
        |								"schema": "title:String, author:String, age:Int",
        |								"count": "10"
        |							},
        |							"customizedProperties": {
        |
        |							}
        |						},
        |						{
        |							"dataCenter" : "http://10.0.90.155:8002",
        |							"name": "MockData-B",
        |							"bundle": "cn.piflow.bundle.common.MockData",
        |							"uuid": "8a80d63f720cdd2301723b7461d92604",
        |							"properties": {
        |								"schema": "title:String, author:String, age:Int",
        |								"count": "10"
        |							},
        |							"customizedProperties": {
        |
        |							}
        |						},
        |						{
        |							"dataCenter" : "",
        |							"name": "Merge-C",
        |							"bundle": "cn.piflow.bundle.common.Merge",
        |							"uuid": "8a80da1b7a8a1327017a9e94e04b0008",
        |							"properties": {
        |								"inports": "data1,data2"
        |							},
        |							"customizedProperties": {
        |
        |							}
        |						},
        |						{
        |							"dataCenter" : "http://10.0.90.119:8001",
        |							"name": "ShowData",
        |							"bundle": "cn.piflow.bundle.external.ShowData",
        |							"uuid": "8a80d63f720cdd2301723b7461d92602",
        |							"properties": {
        |								"showNumber": "5"
        |							},
        |							"customizedProperties": {
        |
        |							}
        |						}
        |					],
        |					"paths": [{
        |						"from": "MockData-A",
        |						"outport": "",
        |						"inport": "data1",
        |						"to": "Merge-C"
        |					},
        |					{
        |						"from": "MockData-B",
        |						"outport": "",
        |						"inport": "data2",
        |						"to": "Merge-C"
        |					},
        |					{
        |						"from": "Merge-C",
        |						"outport": "",
        |						"inport": "",
        |						"to": "ShowData"
        |					}]
        |				}
        |			}
        |
      """.stripMargin*/

    val json0 =
      """
        |{
        |    "flow": {
        |        "name": "flow1",
        |        "executorMemory": "1g",
        |        "executorNumber": "1",
        |        "uuid": "8a80d63f720cdd2301723b7461d92600",
        |        "executorCores": "1",
        |        "driverMemory": "1g",
        |        "environmentVariable": {
        |            "${SPARK_HOME}": "/opt/data/spark/bin",
        |            "${CODE}": "A00101"
        |        },
        |        "stops":[
        |            {
        |                "dataCenter" : "http://10.0.90.155:8002",
        |                "name":"SelectHiveQL-A",
        |                "bundle":"cn.piflow.bundle.hive.SelectHiveQL",
        |                "uuid": "8a80d63f720cdd2301723b7461d92604",
        |                "properties":{
        |                    "hiveQL":"select * from test.student limit 10 "
        |                },
        |                "customizedProperties": {}
        |            },
        |            {
        |                "dataCenter" : "http://10.0.82.42:8002",
        |                "name":"SelectHiveQL-B",
        |                "bundle":"cn.piflow.bundle.hive.SelectHiveQL",
        |                "uuid": "8a80d63f720cdd2301723b7461d92604",
        |                "properties":{
        |                    "hiveQL":"select * from test.score"
        |                },
        |                "customizedProperties": {}
        |            },
        |            {
        |                "dataCenter" : "",
        |                "name":"Join-C",
        |                "bundle":"cn.piflow.bundle.common.Join",
        |                "uuid": "8a80da1b7a8a1327017a9e94e04b0008",
        |                "properties":{
        |                    "correlationColumn": "id",
        |                    "joinMode": "left"
        |                }
        |            },
        |            {
        |                "dataCenter" : "http://10.0.90.119:8001",
        |                "name":"average_score",
        |                "bundle":"cn.piflow.bundle.common.ExecuteSQLStop",
        |                "uuid":"8a80d63f720cdd2301723b7461d9260344",
        |                "properties":{
        |                    "sql":"select id,name,avg(score) from student_score group by id,name",
        |                    "viewName": "student_score"
        |                 },
        |                "customizedProperties": {}
        |            }
        |        ],
        |        "paths":[
        |            {
        |                "from":"SelectHiveQL-A",
        |                "outport":"",
        |                "inport":"Left",
        |                "to":"Join-C"
        |            },
        |            {
        |                "from":"SelectHiveQL-B",
        |                "outport":"",
        |                "inport":"Right",
        |                "to":"Join-C"
        |            },
        |            {
        |                "from":"Join-C",
        |                "outport":"",
        |                "inport":"",
        |                "to":"average_score"
        |
        |            }
        |        ]
        |    }
        |}
      """.stripMargin


    val url = "http://10.0.90.119:8001/datacenter/flow/start"
    val timeout = 1800
    val requestConfig = RequestConfig.custom()
      .setConnectTimeout(timeout*1000)
      .setConnectionRequestTimeout(timeout*1000)
      .setSocketTimeout(timeout*1000).build()

    val client = HttpClientBuilder.create().setDefaultRequestConfig(requestConfig).build()

    val post:HttpPost = new HttpPost(url)
    post.addHeader("Content-Type", "application/json")
    post.setEntity(new StringEntity(json0))


    val response:CloseableHttpResponse = client.execute(post)
    val entity = response.getEntity
    val str = EntityUtils.toString(entity,"UTF-8")
    println("Code is " + str)

    /*val map = OptionUtil.getAny(JSON.parseFull(json))d.asInstanceOf[Map[String, Any]]

    val jsonObj = JsonUtil.toJson(map)
    val str = JsonUtil.format(jsonObj)
    //convertJson = convertJson.replaceAll("\\{","\\{\t\n")


    //var convertJson1 = convertJson.replaceAll("{","{\n")
    //var convertJson2 = convertJson1.replaceAll("}","}\n")
    println("Convert Json===" + str)

    val convertMap = OptionUtil.getAny(JSON.parseFull(str)).asInstanceOf[Map[String, Any]]
    println("Convert Map===" + convertMap)*/


  }

}
