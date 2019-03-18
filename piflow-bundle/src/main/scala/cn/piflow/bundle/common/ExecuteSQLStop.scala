package cn.piflow.bundle.common

import breeze.collection.mutable.ArrayMap
import breeze.linalg.*
import cn.piflow._
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.lib._
import cn.piflow.lib.io.{FileFormat, TextFile}
import org.elasticsearch.common.collect.Tuple


class ExecuteSQLStop extends ConfigurableStop{

  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "Execute sql"
  val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)

  var sql: String = _
  var bundle2TableNames: String = _


  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {


    val tableNames = bundle2TableNames.split(",")
    for (i <- 0 until tableNames.length){


      //   00->table1    ,.....
      if (i== 0){
        val imports = tableNames(i).split("->")(0)
        val tableName = tableNames(i).split("->")(1)
        val  bundle2 = imports -> tableName

        val doMap = new ExecuteSQL(sql,bundle2);
        doMap.perform(in,out,pec)

      } else {
        val imports = tableNames(i).split("->")(0)
        val tableName = tableNames(i).split("->")(1)
        val bundle2:(String,String)  = imports -> tableName

        val doMap = new ExecuteSQL(sql,bundle2);
        doMap.perform(in,out,pec)
      }
    }


  }

  def createCountWords() = {

    val processCountWords = new FlowImpl();
    //SparkProcess = loadStream + transform... + writeStream
    processCountWords.addStop("LoadStream", new LoadStream(TextFile("hdfs://10.0.86.89:9000/yg/2", FileFormat.TEXT)));
    processCountWords.addStop("DoMap", new ExecuteSQLStop);

    processCountWords.addPath(Path.from("LoadStream").to("DoMap"));

    new FlowAsStop(processCountWords);
  }


  override def setProperties(map: Map[String, Any]): Unit = {
    sql = MapUtil.get(map,"sql").asInstanceOf[String]
    bundle2TableNames = MapUtil.get(map,"bundle2TableName").asInstanceOf[String]

  }
  override def initialize(ctx: ProcessContext): Unit = {

  }
  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val sql = new PropertyDescriptor().name("sql").displayName("sql").description("sql").defaultValue("").required(true)
    val bundle2TableNames = new PropertyDescriptor().name("bundle2TableNames").displayName("bundle2TableName").description(" bundle2TableName: (String, String)*) ").defaultValue("").required(true)
    descriptor = sql :: descriptor
    descriptor = bundle2TableNames :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/common/ExecuteSqlStop.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.CommonGroup.toString)
  }



}



