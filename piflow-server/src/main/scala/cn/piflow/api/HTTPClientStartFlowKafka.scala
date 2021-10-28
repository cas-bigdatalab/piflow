package cn.piflow.api

import org.apache.http.client.config.RequestConfig
import org.apache.http.client.methods.{CloseableHttpResponse, HttpPost}
import org.apache.http.entity.StringEntity
import org.apache.http.impl.client.HttpClientBuilder
import org.apache.http.util.EntityUtils

object HTTPClientStartFlowKafka {

  def main(args: Array[String]): Unit = {

    val json =
      """
        |{
        |  "flow":{
        |    "name":"test",
        |    "executorMemory": "1g",
        |    "executorNumber": "1",
        |    "executorCores": "1",
        |    "driverMemory": "1g",
        |    "uuid":"1234",
        |    "stops":[
        |      {
        |        "uuid":"0000",
        |        "name":"SelectHiveQL",
        |        "bundle":"cn.piflow.bundle.hive.SelectHiveQL",
        |        "properties":{
        |          "hiveQL":"select * from sparktest.dblp_phdthesis"
        |        }
        |
        |      },
        |      {
        |        "uuid":"1111",
        |        "name":"WriteToKafka",
        |        "bundle":"cn.piflow.bundle.kafka.WriteToKafka",
        |        "properties":{
        |          "kafka_host":"10.0.86.93:9092,10.0.86.94:9092,10.0.86.95:9092",
        |          "topic":"test_topic1"
        |        }
        |
        |      },
        |      {
        |        "uuid":"2222",
        |        "name":"ReadFromKafka",
        |        "bundle":"cn.piflow.bundle.kafka.ReadFromKafka",
        |        "properties":{
        |          "kafka_host":"10.0.86.93:9092,10.0.86.94:9092,10.0.86.95:9092",
        |          "topic":"test_topic1",
        |          "schema":"title,author,pages"
        |        }
        |
        |      }
        |
        |    ],
        |    "paths":[
        |      {
        |        "from":"SelectHiveQL",
        |        "outport":"",
        |        "inport":"",
        |        "to":"WriteToKafka"
        |      },
        |      {
        |        "from":"WriteToKafka",
        |        "outport":"",
        |        "inport":"",
        |        "to":"ReadFromKafka"
        |      }
        |
        |    ]
        |  }
        |}
        |
      """.stripMargin


    val url = "http://10.0.86.191:8002/flink/yarn-cluster/flow/start"
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
