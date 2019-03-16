package cn.piflow.api

import java.util

import org.apache.commons.httpclient.URI
import org.apache.http.client.methods.{CloseableHttpResponse, HttpGet, HttpPost}
import org.apache.http.impl.client.HttpClients
import org.apache.http.message.BasicNameValuePair
import org.apache.http.util.EntityUtils
import org.omg.CORBA.NameValuePair

object HTTPClientGetFlowInfo {

  def main(args: Array[String]): Unit = {

    val url = "http://10.0.86.98:8001/flow/info??appID=application_1544066083705_0230"
    val client = HttpClients.createDefault()
    val getFlowDebugData:HttpGet = new HttpGet(url)

    val response:CloseableHttpResponse = client.execute(getFlowDebugData)
    val entity = response.getEntity
    val str = EntityUtils.toString(entity,"UTF-8")
    println("Code is " + str)
  }

}
