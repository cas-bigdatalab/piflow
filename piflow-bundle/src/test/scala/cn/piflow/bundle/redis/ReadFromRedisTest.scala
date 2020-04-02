package cn.piflow.bundle.redis

import java.net.InetAddress

import cn.piflow.Runner
import cn.piflow.conf.bean.FlowBean
import cn.piflow.conf.util.{FileUtil, OptionUtil}
import cn.piflow.util.{PropertyUtil, ServerIpUtil}
import org.apache.spark.sql.{SaveMode, SparkSession}
import org.h2.tools.Server
import org.junit.Test

import scala.util.parsing.json.JSON

class ReadFromRedisTest {

  @Test
  def testFlow(): Unit ={

    //parse flow json
    val file = "src/main/resources/flow/redis/ReadFromRedis.json"
    val flowJsonStr = FileUtil.fileReader(file)
    val map = OptionUtil.getAny(JSON.parseFull(flowJsonStr)).asInstanceOf[Map[String, Any]]
    println(map)

    //create flow
    val flowBean = FlowBean(map)
    val flow = flowBean.constructFlow()

    val ip = InetAddress.getLocalHost.getHostAddress

    cn.piflow.util.FileUtil.writeFile("server.ip=" + ip, ServerIpUtil.getServerIpFile())
    val h2Server = Server.createTcpServer("-tcp", "-tcpAllowOthers", "-tcpPort", "50001").start()

    //execute flow
    val spark = SparkSession.builder()
      .master("local[*]")
      .appName("CsvParserTest")
      .config("spark.driver.memory", "1g")
      .config("spark.executor.memory", "2g")
      .config("spark.cores.max", "2")
      .config("hive.metastore.uris",PropertyUtil.getPropertyValue("hive.metastore.uris"))
      .enableHiveSupport()
      .getOrCreate()

    val process = Runner.create()
      .bind(classOf[SparkSession].getName, spark)
      .bind("checkpoint.path", "")
      .bind("debug.path","")
      .start(flow);

    process.awaitTermination();
    val pid = process.pid();
    println(pid + "!!!!!!!!!!!!!!!!!!!!!")
    spark.close();
  }

  @Test
  def testFlow1(): Unit ={

    val spark = SparkSession.builder()
      .master("local[*]")
      .appName("SparkReadRedis")
      .config("spark.driver.memory", "1g")
      .config("spark.executor.memory", "2g")
      .config("spark.cores.max", "2")
      .config("hive.metastore.uris",PropertyUtil.getPropertyValue("hive.metastore.uris"))

      .config("spark.redis.host","192.168.3.138")
      .config("spark.redis.port", "7000")
      .config("spark.redis.auth","bigdata") //指定redis密码
      .config("spark.redis.db","0") //指定redis库
      .enableHiveSupport()
      .getOrCreate()


   val df =  spark.sql("select * from test.user1")

    df.write
      .format("org.apache.spark.sql.redis")
      .option("table", "person")
      .option("key.column", "name")
      .mode(SaveMode.Overwrite)
      .save()


  }

}
