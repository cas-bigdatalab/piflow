package cn.piflow.api

import org.apache.http.client.config.RequestConfig
import org.apache.http.client.methods.{CloseableHttpResponse, HttpGet, HttpPost}
import org.apache.http.entity.StringEntity
import org.apache.http.impl.client.{HttpClientBuilder, HttpClients}
import org.apache.http.util.EntityUtils

object HTTPClientGetScheduleInfo {

  def main(args: Array[String]): Unit = {
    val url = "http://10.0.85.83:8001/schedule/info?scheduleId=schedule_9339f584-4ec5-4e12-a51d-4214182ff63a"
    val client = HttpClients.createDefault()
    val getFlowDebugData:HttpGet = new HttpGet(url)

    val response:CloseableHttpResponse = client.execute(getFlowDebugData)
    val entity = response.getEntity
    val str = EntityUtils.toString(entity,"UTF-8")
    println("Code is " + str)
  }

}
