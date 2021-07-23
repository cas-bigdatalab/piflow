package cn.piflow.util

import org.apache.http.HttpStatus
import org.apache.http.client.config.RequestConfig
import org.apache.http.client.methods.HttpPost
import org.apache.http.entity.StringEntity
import org.apache.http.impl.client.HttpClients
import org.apache.http.util.EntityUtils


object HttpClientsUtil {

  def doPost(url: String, timeoutMs: Int, json: String) : String = {
    // Create client instance
    val httpClient = HttpClients.createDefault()
    // Create post instance
    val post = new HttpPost(url)
    // Set timeout
    val requestConfig = RequestConfig.custom()
      .setConnectionRequestTimeout(timeoutMs*1000)
      .setConnectTimeout(timeoutMs*1000)
      .setSocketTimeout(timeoutMs*1000).build()
    // set requestConfig
    post.setConfig(requestConfig)
    // set request header
    post.addHeader("Content-Type", "application/json")
    // set request entity
    post.setEntity(new StringEntity(json, "UTF-8"))

    // execute request
    val response = httpClient.execute(post)
    val statusCode = response.getStatusLine.getStatusCode
    // Get returned result
    val str = EntityUtils.toString(response.getEntity, "UTF-8")
    if (HttpStatus.SC_INTERNAL_SERVER_ERROR == statusCode) {
      throw new Throwable(str)
    }
    println("Code is " + str)

    str
  }

  def main(args: Array[String]): Unit = {
    val url = "hdfs://127.0.0.1:8001/flow/start"
    val timeoutMs = 1800
    val temp = doPost(url,timeoutMs,"")

  }

}
