package cn.piflow.api

import org.apache.http.client.methods.{CloseableHttpResponse, HttpGet}
import org.apache.http.impl.client.HttpClients
import org.apache.http.util.EntityUtils

object HTTPClientGetDataCenterTaskPlan {

  def main(args: Array[String]): Unit = {

    val url = "http://10.0.90.119:8001/datacenter/flow/taskPlan?groupId=group_9f497ee5-56a1-42e5-8555-fa427ab49c34"
    val client = HttpClients.createDefault()
    val getFlowGroupInfoData:HttpGet = new HttpGet(url)

    val response:CloseableHttpResponse = client.execute(getFlowGroupInfoData)
    val entity = response.getEntity
    val str = EntityUtils.toString(entity,"UTF-8")
    println("Code is " + str)
  }

}
