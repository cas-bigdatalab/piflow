package cn.piflow.api

import org.apache.http.client.config.RequestConfig
import org.apache.http.client.methods.{CloseableHttpResponse, HttpPost}
import org.apache.http.entity.StringEntity
import org.apache.http.impl.client.HttpClientBuilder
import org.apache.http.util.EntityUtils

object HTTPClientScheduleFlowGroup {

  def main(args: Array[String]): Unit = {
    val json =
      """
        |{
        |	"expression": "0 0/5 * * * ?",
        |	"schedule": {
        |		"group": {
        |			"name": "TestFlowGroup",
        |			"uuid": "1111111111111",
        |			"flows": [{
        |					"flow": {
        |						"name": "xml,csv-merge-fork-hive,json,csv",
        |						"uuid": "1234",
        |						"stops": [{
        |								"uuid": "1111",
        |								"name": "XmlParser",
        |								"bundle": "cn.piflow.bundle.xml.XmlParser",
        |								"properties": {
        |									"xmlpath": "hdfs://10.0.86.89:9000/xjzhu/dblp.mini.xml",
        |									"rowTag": "phdthesis"
        |								}
        |							},
        |							{
        |								"uuid": "2222",
        |								"name": "SelectField",
        |								"bundle": "cn.piflow.bundle.common.SelectField",
        |								"properties": {
        |									"schema": "title,author,pages"
        |								}
        |
        |							},
        |							{
        |								"uuid": "3333",
        |								"name": "PutHiveStreaming",
        |								"bundle": "cn.piflow.bundle.hive.PutHiveStreaming",
        |								"properties": {
        |									"database": "sparktest",
        |									"table": "dblp_phdthesis"
        |								}
        |							}
        |						],
        |						"paths": [{
        |								"from": "XmlParser",
        |								"outport": "",
        |								"inport": "",
        |								"to": "SelectField"
        |							},
        |							{
        |								"from": "SelectField",
        |								"outport": "",
        |								"inport": "",
        |								"to": "PutHiveStreaming"
        |							}
        |						]
        |					}
        |				},
        |				{
        |					"flow": {
        |						"name": "another",
        |						"uuid": "5678",
        |						"stops": [{
        |								"uuid": "1111",
        |								"name": "XmlParser",
        |								"bundle": "cn.piflow.bundle.xml.XmlParser",
        |								"properties": {
        |									"xmlpath": "hdfs://10.0.86.89:9000/xjzhu/dblp.mini.xml",
        |									"rowTag": "phdthesis"
        |								}
        |							},
        |							{
        |								"uuid": "2222",
        |								"name": "SelectField",
        |								"bundle": "cn.piflow.bundle.common.SelectField",
        |								"properties": {
        |									"schema": "title,author,pages"
        |								}
        |
        |							},
        |							{
        |								"uuid": "3333",
        |								"name": "PutHiveStreaming",
        |								"bundle": "cn.piflow.bundle.hive.PutHiveStreaming",
        |								"properties": {
        |									"database": "sparktest",
        |									"table": "dblp_phdthesis"
        |								}
        |							}
        |						],
        |						"paths": [{
        |								"from": "XmlParser",
        |								"outport": "",
        |								"inport": "",
        |								"to": "SelectField"
        |							},
        |							{
        |								"from": "SelectField",
        |								"outport": "",
        |								"inport": "",
        |								"to": "PutHiveStreaming"
        |							}
        |						]
        |					}
        |
        |				}
        |			],
        |
        |			"conditions": [{
        |					"entry": "one",
        |					"after": "another"
        |				}
        |
        |			]
        |		}
        |	}
        |}
      """.stripMargin
    val url = "http://10.0.86.98:8001/schedule/start"
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
