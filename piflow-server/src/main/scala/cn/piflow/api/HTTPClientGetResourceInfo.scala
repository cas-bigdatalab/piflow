package cn.piflow.api

import org.apache.http.client.methods.{CloseableHttpResponse, HttpGet}
import org.apache.http.impl.client.HttpClients
import org.apache.http.util.EntityUtils

object HTTPClientGetResourceInfo {

  def main(args: Array[String]): Unit = {

    val url = "http://10.0.85.83:8001/resource/info"
    val client = HttpClients.createDefault()
    val getFlowDebugData:HttpGet = new HttpGet(url)

    val response:CloseableHttpResponse = client.execute(getFlowDebugData)
    val entity = response.getEntity
    val str = EntityUtils.toString(entity,"UTF-8")
    println("Code is " + str)

  }

}
