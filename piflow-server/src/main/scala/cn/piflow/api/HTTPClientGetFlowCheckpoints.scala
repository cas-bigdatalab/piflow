package cn.piflow.api

import org.apache.http.client.methods.{CloseableHttpResponse, HttpGet}
import org.apache.http.impl.client.HttpClients
import org.apache.http.util.EntityUtils

object HTTPClientGetFlowCheckpoints {

  def main(args: Array[String]): Unit = {

    val url = "http://10.0.86.98:8001/flow/checkpoints?appID=process_9e291e46-fe25-4e7c-943d-0ff85dddb22d_1"
    val client = HttpClients.createDefault()
    val getFlowInfo:HttpGet = new HttpGet(url)

    val response:CloseableHttpResponse = client.execute(getFlowInfo)
    val entity = response.getEntity
    val str = EntityUtils.toString(entity,"UTF-8")
    println("Flow checkpoint is " + str)
  }

}
