package cn.piflow.api

import cn.piflow.Runner
import cn.piflow.conf.bean.FlowBean
import org.apache.spark.sql.SparkSession
import cn.piflow.conf.util.{FileUtil, OptionUtil}
import cn.piflow.Process
import cn.piflow.api.util.PropertyUtil
import org.apache.http.client.methods.{CloseableHttpResponse, HttpGet, HttpPost}
import org.apache.http.impl.client.HttpClients
import org.apache.http.util.EntityUtils

import scala.util.parsing.json.JSON

object API {

  def startFlow(flowJson : String):Process = {

    val map = OptionUtil.getAny(JSON.parseFull(flowJson)).asInstanceOf[Map[String, Any]]
    println(map)

    //create flow
    val flowBean = FlowBean(map)
    val flow = flowBean.constructFlow()

    //execute flow
    val spark = SparkSession.builder()
      .master("spark://10.0.86.89:7077")
      .appName(flowBean.name)
      .config("spark.driver.memory", "1g")
      .config("spark.executor.memory", "2g")
      .config("spark.cores.max", "2")
      .config("spark.jars", PropertyUtil.getPropertyValue("piflow.bundle"))
      .enableHiveSupport()
      .getOrCreate()


    val process = Runner.create()
      .bind(classOf[SparkSession].getName, spark)
      .bind("checkpoint.path", PropertyUtil.getPropertyValue("checkpoint.path"))
      .start(flow);

    process.awaitTermination();
    spark.close();
    process
  }

  def stopFlow(process : Process): String = {
    process.stop()
    "ok"
  }

  def getFlowInfo(appID : String) : String = {

    val url = PropertyUtil.getPropertyValue("yarn.url") + appID
    val client = HttpClients.createDefault()
    val get:HttpGet = new HttpGet(url)

    val response:CloseableHttpResponse = client.execute(get)
    val entity = response.getEntity
    val str = EntityUtils.toString(entity,"UTF-8")
    println("Code is " + str)
    str
  }

}
