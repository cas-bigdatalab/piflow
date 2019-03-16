package cn.piflow.api

import org.apache.http.client.methods.{CloseableHttpResponse, HttpGet}
import org.apache.http.impl.client.HttpClients
import org.apache.http.util.EntityUtils

object HTTPClientGetFlowDebugData {

  def main(args: Array[String]): Unit = {

    val url = "http://10.0.86.98:8001/flow/debugData?processID=process_cf1bab97-8eaf-4b3a-82a2-6a0eaa2a9ed4_1&stopName=Merge&port=default"
    val client = HttpClients.createDefault()
    val getFlowInfo:HttpGet = new HttpGet(url)

    val response:CloseableHttpResponse = client.execute(getFlowInfo)
    val entity = response.getEntity
    val str = EntityUtils.toString(entity,"UTF-8")
    println( str)
  }
}
