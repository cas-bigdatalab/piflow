package cn.piflow.api
import org.apache.http.client.config.RequestConfig
import org.apache.http.client.methods.{CloseableHttpResponse, HttpGet, HttpPost}
import org.apache.http.entity.StringEntity
import org.apache.http.impl.client.{HttpClientBuilder, HttpClients}
import org.apache.http.util.EntityUtils

object HTTPClientMonitor {

  def main(args: Array[String]): Unit = {

    val url = "http://127.0.0.1:8001/monitor/throughout?appId=a&stopName=b&portName=c"
    val client = HttpClients.createDefault()
    val getFlowDebugData: HttpGet = new HttpGet(url)
    val response: CloseableHttpResponse = client.execute(getFlowDebugData)
    val entity = response.getEntity
    val str = EntityUtils.toString(entity, "UTF-8")
    println("Code is " + str  +"  test succesfully")
  }
}
