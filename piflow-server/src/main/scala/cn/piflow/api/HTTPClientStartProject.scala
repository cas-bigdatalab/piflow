package cn.piflow.api

import org.apache.http.client.config.RequestConfig
import org.apache.http.client.methods.{CloseableHttpResponse, HttpPost}
import org.apache.http.entity.StringEntity
import org.apache.http.impl.client.HttpClientBuilder
import org.apache.http.util.EntityUtils

object HTTPClientStartProject {

  def main(args: Array[String]): Unit = {

    val json =
      """
        |{
        |	"project": {
        |		"name": "TestProject",
        |		"uuid": "1111111111111",
        |		"groups": [{
        |			"group": {
        |				"name": "FlowGroup",
        |				"uuid": "1111111111111",
        |				"flows": [{
        |						"flow": {
        |							"name": "one",
        |							"uuid": "1234",
        |							"executorNumber": "2",
        |							"executorMemory": "1g",
        |							"executorCores": "1",
        |							"stops": [{
        |									"uuid": "1111",
        |									"name": "XmlParser",
        |									"bundle": "cn.piflow.bundle.xml.XmlParser",
        |									"properties": {
        |										"xmlpath": "hdfs://10.0.86.89:9000/xjzhu/dblp.mini.xml",
        |										"rowTag": "phdthesis"
        |									}
        |								},
        |								{
        |									"uuid": "2222",
        |									"name": "SelectField",
        |									"bundle": "cn.piflow.bundle.common.SelectField",
        |									"properties": {
        |										"schema": "title,author,pages"
        |									}
        |
        |								},
        |								{
        |									"uuid": "3333",
        |									"name": "PutHiveStreaming",
        |									"bundle": "cn.piflow.bundle.hive.PutHiveStreaming",
        |									"properties": {
        |										"database": "sparktest",
        |										"table": "dblp_phdthesis"
        |									}
        |								}
        |							],
        |							"paths": [{
        |									"from": "XmlParser",
        |									"outport": "",
        |									"inport": "",
        |									"to": "SelectField"
        |								},
        |								{
        |									"from": "SelectField",
        |									"outport": "",
        |									"inport": "",
        |									"to": "PutHiveStreaming"
        |								}
        |							]
        |						}
        |					},
        |					{
        |						"flow": {
        |							"name": "two",
        |							"uuid": "5678",
        |							"stops": [{
        |									"uuid": "1111",
        |									"name": "XmlParser",
        |									"bundle": "cn.piflow.bundle.xml.XmlParser",
        |									"properties": {
        |										"xmlpath": "hdfs://10.0.86.89:9000/xjzhu/dblp.mini.xml",
        |										"rowTag": "phdthesis"
        |									}
        |								},
        |								{
        |									"uuid": "2222",
        |									"name": "SelectField",
        |									"bundle": "cn.piflow.bundle.common.SelectField",
        |									"properties": {
        |										"schema": "title,author,pages"
        |									}
        |
        |								},
        |								{
        |									"uuid": "3333",
        |									"name": "PutHiveStreaming",
        |									"bundle": "cn.piflow.bundle.hive.PutHiveStreaming",
        |									"properties": {
        |										"database": "sparktest",
        |										"table": "dblp_phdthesis"
        |									}
        |								}
        |							],
        |							"paths": [{
        |									"from": "XmlParser",
        |									"outport": "",
        |									"inport": "",
        |									"to": "SelectField"
        |								},
        |								{
        |									"from": "SelectField",
        |									"outport": "",
        |									"inport": "",
        |									"to": "PutHiveStreaming"
        |								}
        |							]
        |						}
        |
        |					}
        |				],
        |
        |				"conditions": [{
        |					"entry": "two",
        |					"after": "one"
        |				}]
        |			}
        |		}],
        |		"flows": [{
        |			"flow": {
        |				"name": "three",
        |				"uuid": "91011",
        |				"executorNumber": "2",
        |				"executorMemory": "1g",
        |				"executorCores": "1",
        |				"stops": [{
        |						"uuid": "1111",
        |						"name": "XmlParser",
        |						"bundle": "cn.piflow.bundle.xml.XmlParser",
        |						"properties": {
        |							"xmlpath": "hdfs://10.0.86.89:9000/xjzhu/dblp.mini.xml",
        |							"rowTag": "phdthesis"
        |						}
        |					},
        |					{
        |						"uuid": "2222",
        |						"name": "SelectField",
        |						"bundle": "cn.piflow.bundle.common.SelectField",
        |						"properties": {
        |							"schema": "title,author,pages"
        |						}
        |
        |					},
        |					{
        |						"uuid": "3333",
        |						"name": "PutHiveStreaming",
        |						"bundle": "cn.piflow.bundle.hive.PutHiveStreaming",
        |						"properties": {
        |							"database": "sparktest",
        |							"table": "dblp_phdthesis"
        |						}
        |					}
        |				],
        |				"paths": [{
        |						"from": "XmlParser",
        |						"outport": "",
        |						"inport": "",
        |						"to": "SelectField"
        |					},
        |					{
        |						"from": "SelectField",
        |						"outport": "",
        |						"inport": "",
        |						"to": "PutHiveStreaming"
        |					}
        |				]
        |			}
        |		}],
        |		"conditions": [{
        |			"entry": "three",
        |			"after": "FlowGroup"
        |		}]
        |	}
        |}
      """.stripMargin

    val url = "http://10.0.86.98:8001/project/start"
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
