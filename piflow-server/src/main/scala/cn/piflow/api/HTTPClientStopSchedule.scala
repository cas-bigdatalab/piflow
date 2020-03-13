package cn.piflow.api

import org.apache.http.client.methods.{CloseableHttpResponse, HttpPost}
import org.apache.http.entity.StringEntity
import org.apache.http.impl.client.HttpClients
import org.apache.http.util.EntityUtils

object HTTPClientStopSchedule {
  def main(args: Array[String]): Unit = {
    val json = """{"scheduleId":"schedule_badbf32a-674d-42a9-8e13-e91ae1539e01"}"""
    val url = "http://10.0.88.13:8002/schedule/stop"
    val client = HttpClients.createDefault()
    val post:HttpPost = new HttpPost(url)

    post.addHeader("Content-Type", "application/json")
    post.setEntity(new StringEntity(json))

    val response:CloseableHttpResponse = client.execute(post)
    val entity = response.getEntity
    val str = EntityUtils.toString(entity,"UTF-8")
    println(str)
  }

}
