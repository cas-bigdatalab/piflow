package cn.piflow.api

import org.apache.http.client.methods.{CloseableHttpResponse, HttpGet}
import org.apache.http.impl.client.HttpClients
import org.apache.http.util.EntityUtils

object HTTPClientGetVisualizationData {

  def main(args: Array[String]): Unit = {
    //
    val url = "http://10.0.90.119:8001/flow/visualizationData?appID=application_1596710850427_0035&stopName=LineChart"
    val client = HttpClients.createDefault()
    val getFlowInfo:HttpGet = new HttpGet(url)

    val response:CloseableHttpResponse = client.execute(getFlowInfo)
    val entity = response.getEntity
    val str = EntityUtils.toString(entity,"UTF-8")
    println( str)
  }
}
