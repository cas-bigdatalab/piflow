package cn.piflow.api

import org.apache.http.client.methods.{CloseableHttpResponse, HttpGet}
import org.apache.http.impl.client.HttpClients
import org.apache.http.util.EntityUtils

object HTTPClientGetFlowGroupInfo {

  def main(args: Array[String]): Unit = {

    val url = "http://10.0.85.83:8001/group/info?groupId=group_91198855-afbc-4726-856f-31326173a90f"
    val client = HttpClients.createDefault()
    val getFlowGroupInfoData:HttpGet = new HttpGet(url)

    val response:CloseableHttpResponse = client.execute(getFlowGroupInfoData)
    val entity = response.getEntity
    val str = EntityUtils.toString(entity,"UTF-8")
    println("Code is " + str)
  }

}
