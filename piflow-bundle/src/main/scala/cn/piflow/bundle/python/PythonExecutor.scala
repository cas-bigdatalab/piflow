package cn.piflow.bundle.python

import java.util
import java.util.UUID

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.util.FileUtil
import jep.Jep
import org.apache.spark.sql.types.{StringType, StructField, StructType}
import org.apache.spark.sql.{DataFrame, Encoders, Row, SparkSession}

import scala.collection.mutable.HashMap
import scala.collection.JavaConversions._

/**
  * Created by xjzhu@cnic.cn on 2/24/20
  */
class PythonExecutor extends ConfigurableStop{
  override val authorEmail: String = "xjzhu@cnic.cn"
  override val description: String = "Execute python script"
  override val inportList: List[String] = List(PortEnum.DefaultPort)
  override val outportList: List[String] = List(PortEnum.DefaultPort)

  var script : String = _
  var execFunction : String = _

  override def setProperties(map: Map[String, Any]): Unit = {
    script = MapUtil.get(map,"script").asInstanceOf[String]
    execFunction = MapUtil.get(map,"execFunction").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val script = new PropertyDescriptor().name("script").displayName("script").description("The code of python").defaultValue("").required(true)
    val execFunction = new PropertyDescriptor().name("execFunction").displayName("execFunction").description("The function of python script to be executed.").defaultValue("").required(true)
    descriptor = script :: descriptor
    descriptor = execFunction :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/python/python.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.Python)
  }
  override def initialize(ctx: ProcessContext): Unit = {}

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val spark = pec.get[SparkSession]()
    import spark.implicits._

    val df = in.read()

    val jep = new Jep()
    val scriptPath = "/tmp/pythonExcutor-"+ UUID.randomUUID() +".py"
    FileUtil.writeFile(script,scriptPath)
    jep.runScript(scriptPath)


    val listInfo = df.toJSON.collectAsList()
    jep.eval(s"result = $execFunction($listInfo)")
    val resultArrayList = jep.getValue("result",new util.ArrayList().getClass)
    println(resultArrayList)


    var resultList = List[Map[String, Any]]()
    val it = resultArrayList.iterator()
    while(it.hasNext){
      val i = it.next().asInstanceOf[java.util.HashMap[String, Any]]
      val item =  mapAsScalaMap(i).toMap[String, Any]
      resultList =  item +: resultList
    }


    val rows = resultList.map( m => Row(m.values.toSeq:_*))
    val header = resultList.head.keys.toList
    val schema = StructType(header.map(fieldName => new StructField(fieldName, StringType, true)))

    val rdd = spark.sparkContext.parallelize(rows)
    val resultDF = spark.createDataFrame(rdd, schema)

    out.write(resultDF)
  }
}
