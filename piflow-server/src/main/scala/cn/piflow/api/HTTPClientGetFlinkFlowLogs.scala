package cn.piflow.api

import org.apache.http.client.methods.{CloseableHttpResponse, HttpGet}
import org.apache.http.impl.client.HttpClients
import org.apache.http.util.EntityUtils

object HTTPClientGetFlinkFlowLogs {

  def main(args: Array[String]): Unit = {

    val url = "http://223.193.3.32:8001/flink/flow/log?appID=application_1613819551288_0196"
    val client = HttpClients.createDefault()
    val getFlowDebugData:HttpGet = new HttpGet(url)

    val response:CloseableHttpResponse = client.execute(getFlowDebugData)
    val entity = response.getEntity
    val str = EntityUtils.toString(entity,"UTF-8")
    println("Code is " + str)
  }

}
