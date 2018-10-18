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

    val url = "http://10.0.86.98:8002/flow/info?appID=application_1539588927382_0016"
    val client = HttpClients.createDefault()
    val getFlowInfo:HttpGet = new HttpGet(url)

    val response:CloseableHttpResponse = client.execute(getFlowInfo)
    val entity = response.getEntity
    val str = EntityUtils.toString(entity,"UTF-8")
    println("Code is " + str)
  }

}
