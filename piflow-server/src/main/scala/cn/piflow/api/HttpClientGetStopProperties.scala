package cn.piflow.api

import org.apache.http.client.methods.{CloseableHttpResponse, HttpGet}
import org.apache.http.impl.client.HttpClients
import org.apache.http.util.EntityUtils

object HttpClientGetStopProperties {

  def main(args: Array[String]): Unit = {

    val url = "http://10.0.86.98:8001/stop/properties?bundle=cn.piflow.bundle.ftp.LoadFromFtp2"
    val client = HttpClients.createDefault()
    val getFlowInfo:HttpGet = new HttpGet(url)

    val response:CloseableHttpResponse = client.execute(getFlowInfo)
    val entity = response.getEntity
    val str = EntityUtils.toString(entity,"UTF-8")
    println("Property Desc is " + str)
  }

}
