package cn.piflow.api

import org.apache.http.client.methods.{CloseableHttpResponse, HttpGet}
import org.apache.http.impl.client.HttpClients
import org.apache.http.util.EntityUtils

object HTTPClientGetFlowGroupInfo {

  def main(args: Array[String]): Unit = {

    val url = "http://10.0.86.98:8001/flowGroup/info?groupId=group_9b41bab2-7c3a-46ec-b716-93b636545e5e"
    val client = HttpClients.createDefault()
    val getFlowGroupInfoData:HttpGet = new HttpGet(url)

    val response:CloseableHttpResponse = client.execute(getFlowGroupInfoData)
    val entity = response.getEntity
    val str = EntityUtils.toString(entity,"UTF-8")
    println("Code is " + str)
  }

}
