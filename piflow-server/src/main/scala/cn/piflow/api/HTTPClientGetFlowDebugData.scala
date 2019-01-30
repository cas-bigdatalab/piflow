package cn.piflow.api

import org.apache.http.client.methods.{CloseableHttpResponse, HttpGet}
import org.apache.http.impl.client.HttpClients
import org.apache.http.util.EntityUtils

object HTTPClientGetFlowDebugData {

  def main(args: Array[String]): Unit = {

    val url = "http://10.0.86.98:8001/flow/debugData?processID=process_104b9840-c163-4a38-bafb-749d2d66b8ad_1&stopName=Merge&port=default"
    val client = HttpClients.createDefault()
    val getFlowInfo:HttpGet = new HttpGet(url)

    val response:CloseableHttpResponse = client.execute(getFlowInfo)
    val entity = response.getEntity
    val str = EntityUtils.toString(entity,"UTF-8")
    println("Code is " + str)
  }
}
