package cn.piflow.api

import cn.piflow.Runner
import cn.piflow.conf.bean.{FlowBean, PropertyDescriptor}
import org.apache.spark.sql.SparkSession
import cn.piflow.conf.util.{ClassUtil, FileUtil, OptionUtil}
import cn.piflow.Process
import cn.piflow.api.util.PropertyUtil
import cn.piflow.conf.util.ClassUtil.findConfigurableStopPropertyDescriptor
import org.apache.http.client.methods.{CloseableHttpResponse, HttpGet, HttpPost}
import org.apache.http.impl.client.HttpClients
import org.apache.http.util.EntityUtils


import scala.util.parsing.json.JSON

object API {

  def startFlow(flowJson : String):(String,Process) = {

    val map = OptionUtil.getAny(JSON.parseFull(flowJson)).asInstanceOf[Map[String, Any]]
    println(map)

    //create flow
    val flowBean = FlowBean(map)
    val flow = flowBean.constructFlow()

    //execute flow
    val spark = SparkSession.builder()
      .master(PropertyUtil.getPropertyValue("spark.master"))
      .appName(flowBean.name)
      .config("spark.deploy.mode",PropertyUtil.getPropertyValue("spark.deploy.mode"))
      .config("spark.hadoop.yarn.resourcemanager.hostname", PropertyUtil.getPropertyValue("yarn.resourcemanager.hostname"))
      .config("spark.hadoop.yarn.resourcemanager.address", PropertyUtil.getPropertyValue("yarn.resourcemanager.address"))
      .config("spark.yarn.access.namenode", PropertyUtil.getPropertyValue("yarn.access.namenode"))
      .config("spark.yarn.stagingDir", PropertyUtil.getPropertyValue("yarn.stagingDir"))
      .config("spark.yarn.jars", PropertyUtil.getPropertyValue("yarn.jars"))
      //.config("spark.driver.memory", "1g")
      //.config("spark.executor.memory", "1g")
      //.config("spark.cores.max", "2")
      .config("spark.jars", PropertyUtil.getPropertyValue("piflow.bundle"))
      .config("hive.metastore.uris",PropertyUtil.getPropertyValue("hive.metastore.uris"))
      .enableHiveSupport()
      .getOrCreate()


    val process = Runner.create()
      .bind(classOf[SparkSession].getName, spark)
      .bind("checkpoint.path", PropertyUtil.getPropertyValue("checkpoint.path"))
      .start(flow);
    val applicationId = spark.sparkContext.applicationId
    //process.awaitTermination();
    //spark.close();
    new Thread( new WaitProcessTerminateRunnable(spark, process)).start()
    (applicationId,process)
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

  def getStopProperties(bundle : String) : String = {
    try{

      val propertyDescriptorList = findConfigurableStopPropertyDescriptor(bundle)
      var propertyJsonList = List[String]()
      propertyDescriptorList.foreach( p => propertyJsonList = p.toJson() +: propertyJsonList  )
      val start ="""{"properties":["""
      val end = """]}"""
      val str = propertyJsonList.mkString(start, ",", end)
      str
    }catch{
      case ex : Exception => println(ex);throw ex
    }

  }

}

class WaitProcessTerminateRunnable(spark : SparkSession, process: Process) extends Runnable  {
  override def run(): Unit = {
    process.awaitTermination()
    spark.close()
  }
}
