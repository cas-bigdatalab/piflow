package cn.piflow.bundle

import java.nio.charset.Charset
import cn.piflow.bundle.common.{DoFlatMapStop, DoMapStop, ExecuteSQLStop}
import cn.piflow.{FlowAsStop, FlowImpl, Path, Runner}
import cn.piflow.lib._
import cn.piflow.lib.io.{FileFormat, TextFile}
import org.apache.flume.api.{RpcClient, RpcClientFactory}
import org.apache.flume.event.EventBuilder
import org.apache.spark.sql.SparkSession
import org.h2.tools.Server
import org.junit.Test

import scala.util.parsing.json.JSON

class DoMapTest {

  @Test
  def testFlowA() {
    val flow = new FlowImpl();
    flow.addStop("CountWords",createProcessCountWords);

    val h2Server = Server.createTcpServer("-tcp", "-tcpAllowOthers", "-tcpPort","50001").start()
    //execute flow
    val spark = SparkSession.builder.master("local[4]")
      .getOrCreate();

    val process = Runner.create()
      .bind(classOf[SparkSession].getName, spark)
      .start(flow);

    process.awaitTermination();
    spark.close();
  }

  val SCRIPT_1 =
    """
		function (row) {
			return $.Row(row.get(0).replaceAll("[\\x00-\\xff]|，|。|：|．|“|”|？|！|　", ""));
		}
    """;
  val SCRIPT_2 =
    """
		function (row) {
			var arr = $.Array();
			var str = row.get(0);
			var len = str.length;
			for (var i = 0; i < len - 1; i++) {
				arr.add($.Row(str.substring(i, i + 2)));
			}

			return arr;
		}
    """;

  val selectSQLParameters : Map[String, String] = Map("sql" -> "select value, count(*) count from table1 group by value order by count desc"
                          ,"bundle2TableName" -> "->table1,->table1")
  val fun1: Map[String, String] = Map("SCRIPT_1" -> SCRIPT_1)
  val fun2: Map[String, String] = Map("SCRIPT_2" -> SCRIPT_2)

  //var bundle2TableName: (String, String) = "" -> "table1"

  def createProcessCountWords() = {

    val doMap = new DoMapStop
    doMap.setProperties(fun1)

    val doFlat = new DoFlatMapStop
    doFlat.setProperties(fun2)

    val executeSQLStop = new ExecuteSQLStop
    executeSQLStop.setProperties(selectSQLParameters)

    val processCountWords = new FlowImpl();
    //SparkProcess = loadStream + transform... + writeStream
    processCountWords.addStop("LoadStream", new LoadStream(TextFile("hdfs://10.0.86.89:9000/xjzhu/honglou.txt", FileFormat.TEXT)));
    processCountWords.addStop("DoMap", doMap);
    processCountWords.addStop("DoFlatMap", doFlat);
    processCountWords.addStop("ExecuteSQL", executeSQLStop);

    processCountWords.addPath(Path.from("LoadStream").to("DoMap").to("DoFlatMap").to("ExecuteSQL"));

    new FlowAsStop(processCountWords);
  }





  @Test
  def flume(): Unit ={
    val client = RpcClientFactory.getDefaultInstance(HOST_NAME,8888)
    while(true) {
      for (i <- 0 to 100) {
        sendDateToFlume(client, "msg" + i)
      }
    }
  }

  val HOST_NAME="master"
  val POST =	8888


  def sendDateToFlume(client:RpcClient,msg:String)={

    val event=  EventBuilder.withBody(msg,Charset.forName("utf-8"))
    client.append(event)
  }


}
