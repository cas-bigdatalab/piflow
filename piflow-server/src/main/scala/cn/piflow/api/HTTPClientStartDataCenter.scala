package cn.piflow.api

import org.apache.http.client.config.RequestConfig
import org.apache.http.client.methods.{CloseableHttpResponse, HttpPost}
import org.apache.http.entity.StringEntity
import org.apache.http.impl.client.HttpClientBuilder
import org.apache.http.util.EntityUtils

object HTTPClientStartDataCenter {

  def main(args: Array[String]): Unit = {

    val json =
      """
        |{
        |	"group": {
        |		"name": "xjzhu",
        |		"flows": [{
        |				"flow": {
        |					"dataCenter": "http://10.0.90.119:8001",
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
        |					"stops": [{
        |							"name": "MockData",
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
        |							"name": "flow1-FlowOutportWriter",
        |							"bundle": "cn.piflow.bundle.FlowPort.FlowOutportWriter",
        |							"uuid": "8a80d63f720cdd2301723b7461d92602",
        |							"properties": {},
        |							"customizedProperties": {
        |
        |							}
        |						}
        |					],
        |					"paths": [{
        |						"inport": "",
        |						"from": "MockData",
        |						"to": "flow1-FlowOutportWriter",
        |						"outport": ""
        |					}]
        |				}
        |			},
        |			{
        |				"flow": {
        |					"dataCenter": "http://10.0.90.119:8001",
        |					"name": "flow2",
        |					"executorMemory": "1g",
        |					"executorNumber": "1",
        |					"uuid": "8a80d63f720cdd2301723b7461d92601",
        |					"executorCores": "1",
        |					"driverMemory": "1g",
        |					"environmentVariable": {
        |						"${SPARK_HOME}": "/opt/data/spark/bin",
        |						"${CODE}": "A00101"
        |					},
        |					"stops": [{
        |							"name": "MockData",
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
        |							"name": "flow2-FlowOutportWriter",
        |							"bundle": "cn.piflow.bundle.FlowPort.FlowOutportWriter",
        |							"uuid": "8a80d63f720cdd2301723b7461d92602",
        |							"properties": {},
        |							"customizedProperties": {
        |
        |							}
        |						}
        |					],
        |					"paths": [{
        |						"inport": "",
        |						"from": "MockData",
        |						"to": "flow2-FlowOutportWriter",
        |						"outport": ""
        |					}]
        |				}
        |			},
        |			{
        |				"flow": {
        |					"dataCenter":"http://10.0.90.119:8001",
        |					"name": "flow3",
        |					"executorMemory": "1g",
        |					"executorNumber": "1",
        |					"uuid": "8a80d63f720cdd2301723b7461d92600",
        |					"executorCores": "1",
        |					"driverMemory": "1g",
        |					"environmentVariable": {
        |						"${SPARK_HOME}": "/opt/data/spark/bin",
        |						"${CODE}": "A00101"
        |					},
        |					"stops": [{
        |							"name": "flow3-FlowInportReader-1",
        |							"bundle": "cn.piflow.bundle.FlowPort.FlowInportReader",
        |							"uuid": "8a80d63f720cdd2301723b7461d92605",
        |							"properties": {
        |								"dataSource": ""
        |							},
        |							"customizedProperties": {
        |
        |							}
        |						},
        |						{
        |							"name": "flow3-FlowInportReader-2",
        |							"bundle": "cn.piflow.bundle.FlowPort.FlowInportReader",
        |							"uuid": "8a80d63f720cdd2301723b7461d92606",
        |							"properties": {
        |								"dataSource": ""
        |							},
        |							"customizedProperties": {
        |
        |							}
        |						},
        |						{
        |							"name": "Merge",
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
        |
        |						"from": "flow3-FlowInportReader-1",
        |						"outport": "",
        |						"inport": "data1",
        |						"to": "Merge"
        |
        |					},
        |					{
        |						"from": "flow3-FlowInportReader-2",
        |						"outport": "",
        |						"inport": "data2",
        |						"to": "Merge"
        |					},
        |					{
        |						"inport": "",
        |						"from": "Merge",
        |						"to": "ShowData",
        |						"outport": ""
        |					}]
        |				}
        |			}
        |
        |		],
        |		"conditions": [{
        |			"after": {
        |       "dataCenter" : "http://10.0.90.119:8001",
        |       "flowName" : "flow1"
        |     },
        |     "outport" : "flow1-FlowOutportWriter",
        |     "inport" : "flow3-FlowInportReader-1",
        |			"entry": {
        |       "dataCenter" : "http://10.0.90.119:8001",
        |       "flowName" : "flow3"
        |     }
        |		},
        |		{
        |			"after": {
        |       "dataCenter" : "http://10.0.90.119:8001",
        |       "flowName" : "flow2"
        |     },
        |     "outport" : "flow2-FlowOutportWriter",
        |     "inport" : "flow3-FlowInportReader-2",
        |			"entry": {
        |       "dataCenter" : "http://10.0.90.119:8001",
        |       "flowName" : "flow3"
        |     }
        |		}],
        |		"uuid": "8a80d88d712aa8c601717c68f71e0268"
        |	}
        |}
      """.stripMargin


    val json2 =
      """
        |{
        |	"flow":{
        |		"executorNumber":"1",
        |		"executorMemory":"1g",
        |		"driverMemory":"1g",
        |		"paths":[
        |			{
        |				"inport":"data1",
        |				"from":"flow3-FlowInportReader-1",
        |				"to":"Merge",
        |				"outport":""
        |			},
        |			{
        |				"inport":"data2",
        |				"from":"flow3-FlowInportReader-2",
        |				"to":"Merge",
        |				"outport":""
        |			},
        |			{
        |				"inport":"",
        |				"from":"Merge",
        |				"to":"ShowData",
        |				"outport":""
        |			}
        |		],
        |		"executorCores":"1",
        |		"name":"flow3",
        |		"dataCenter":"http://10.0.90.119:8001",
        |		"stops":[
        |			{
        |				"customizedProperties":{},
        |				"name":"flow3-FlowInportReader-1",
        |				"bundle":"cn.piflow.bundle.FlowPort.FlowInportReader",
        |				"uuid":"8a80d63f720cdd2301723b7461d92605",
        |				"properties":{
        |					"dataSource":"hdfs://10.0.90.155:9000/user/piflow/dataCenter//application_1627523264894_0006/flow1-FlowOutportWriter"
        |				}
        |			},
        |			{
        |				"customizedProperties":{},
        |				"name":"flow3-FlowInportReader-2",
        |				"bundle":"cn.piflow.bundle.FlowPort.FlowInportReader",
        |				"uuid":"8a80d63f720cdd2301723b7461d92606",
        |				"properties":{
        |					"dataSource":"hdfs://10.0.90.155:9000/user/piflow/dataCenter//application_1627523264894_0005/flow2-FlowOutportWriter"
        |				}
        |			},
        |			{
        |				"customizedProperties":{},
        |				"name":"Merge",
        |				"bundle":"cn.piflow.bundle.common.Merge",
        |				"uuid":"8a80da1b7a8a1327017a9e94e04b0008",
        |				"properties":{
        |					"inports":"data1,data2"
        |				}
        |			},
        |			{
        |				"customizedProperties":{},
        |				"name":"ShowData",
        |				"bundle":"cn.piflow.bundle.external.ShowData",
        |				"uuid":"8a80d63f720cdd2301723b7461d92602",
        |				"properties":{
        |					"showNumber":"5"
        |				}
        |			}
        |		],
        |		"environmentVariable":{
        |			"${CODE}":"A00101",
        |			"${SPARK_HOME}":"/opt/data/spark/bin"
        |		},
        |		"uuid":"8a80d63f720cdd2301723b7461d92600"
        |	}
        |}
      """.stripMargin
    val url = "http://10.0.90.119:8001/datacenter/group/start"
    //val url = "http://10.0.90.119:8001/flow/start"
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
