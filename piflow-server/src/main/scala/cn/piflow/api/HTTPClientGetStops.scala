package cn.piflow.api

import org.apache.http.client.methods.{CloseableHttpResponse, HttpGet}
import org.apache.http.impl.client.HttpClients
import org.apache.http.util.EntityUtils

object HTTPClientGetStops {
  def main(args: Array[String]): Unit = {

    val url = "http://10.0.86.98:8002/stop/listWithGroup"
    //val url = "http://10.0.86.98:8001/stop/list"
    val client = HttpClients.createDefault()
    val getGroups:HttpGet = new HttpGet(url)

    val response:CloseableHttpResponse = client.execute(getGroups)
    val entity = response.getEntity
    val str = EntityUtils.toString(entity,"UTF-8")
    println("Groups is: " + str)
  }

}
