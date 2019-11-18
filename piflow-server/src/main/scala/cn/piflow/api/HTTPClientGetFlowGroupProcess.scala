package cn.piflow.api

import org.apache.http.client.methods.{CloseableHttpResponse, HttpGet}
import org.apache.http.impl.client.HttpClients
import org.apache.http.util.EntityUtils

object HTTPClientGetFlowGroupProcess {

  def main(args: Array[String]): Unit = {

    val url = "http://10.0.86.98:8001/flowGroup/progress?groupId=group_15a89eb4-c4fa-45f2-bda5-46c4096053c0"
    val client = HttpClients.createDefault()
    val getFlowGroupProgressData:HttpGet = new HttpGet(url)

    val response:CloseableHttpResponse = client.execute(getFlowGroupProgressData)
    val entity = response.getEntity
    val str = EntityUtils.toString(entity,"UTF-8")
    println("Code is " + str)
  }

}
