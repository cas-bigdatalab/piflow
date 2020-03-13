package cn.piflow.api

import org.apache.http.client.methods.{CloseableHttpResponse, HttpGet}
import org.apache.http.impl.client.HttpClients
import org.apache.http.util.EntityUtils

object HTTPClientGetFlowDebugData {

  def main(args: Array[String]): Unit = {
    //
    val url = "http://10.0.86.191:8002/flow/debugData?appID=application_1562293222869_0090&stopName=Fork&port=out3"
    val client = HttpClients.createDefault()
    val getFlowInfo:HttpGet = new HttpGet(url)

    val response:CloseableHttpResponse = client.execute(getFlowInfo)
    val entity = response.getEntity
    val str = EntityUtils.toString(entity,"UTF-8")
    println( str)
  }
}
