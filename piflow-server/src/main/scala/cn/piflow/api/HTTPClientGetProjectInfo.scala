package cn.piflow.api

import org.apache.http.client.methods.{CloseableHttpResponse, HttpGet}
import org.apache.http.impl.client.HttpClients
import org.apache.http.util.EntityUtils

object HTTPClientGetProjectInfo {

  def main(args: Array[String]): Unit = {

    val url = "http://10.0.86.98:8001/project/info?projectId=project_9ababcea-0e5c-4825-a005-4591c09ec9c4"
    val client = HttpClients.createDefault()
    val getFlowGroupInfoData:HttpGet = new HttpGet(url)

    val response:CloseableHttpResponse = client.execute(getFlowGroupInfoData)
    val entity = response.getEntity
    val str = EntityUtils.toString(entity,"UTF-8")
    println("Code is " + str)
  }

}
