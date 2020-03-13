package cn.piflow.api

import org.apache.http.client.methods.{CloseableHttpResponse, HttpGet}
import org.apache.http.impl.client.HttpClients
import org.apache.http.util.EntityUtils

object HTTPClientGetFlowGroupProcess {

  def main(args: Array[String]): Unit = {

    val url = "http://10.0.85.83:8001/group/progress?groupId=group_527ff279-a278-41b0-a658-7595a576fbb9"
    val client = HttpClients.createDefault()
    val getFlowGroupProgressData:HttpGet = new HttpGet(url)

    val response:CloseableHttpResponse = client.execute(getFlowGroupProgressData)
    val entity = response.getEntity
    val str = EntityUtils.toString(entity,"UTF-8")
    println("Code is " + str)
  }

}
