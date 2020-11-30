package cn.piflow.bundle.script

import java.util
import java.util.UUID

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Language, Port, StopGroup}
import cn.piflow.util.FileUtil
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import jep.Jep
import org.apache.spark.sql.types.{StringType, StructField, StructType}
import org.apache.spark.sql.{Row, SparkSession}

import scala.collection.JavaConversions._

/**
  * Created by xjzhu@cnic.cn on 2/24/20
  */
class ExecutePythonWithDataFrame extends ConfigurableStop{
  override val authorEmail: String = "xjzhu@cnic.cn"
  override val description: String = "Execute python script with dataframe"
  override val inportList: List[String] = List(Port.DefaultPort)
  override val outportList: List[String] = List(Port.DefaultPort)

  var script : String = _
  var execFunction : String = _

  override def setProperties(map: Map[String, Any]): Unit = {
    script = MapUtil.get(map,"script").asInstanceOf[String]
    execFunction = MapUtil.get(map,"execFunction").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val script = new PropertyDescriptor()
      .name("script")
      .displayName("script")
      .description("The code of python")
      .defaultValue("")
      .required(true)
      .language(Language.Python)
    val execFunction = new PropertyDescriptor()
      .name("execFunction")
      .displayName("execFunction")
      .description("The function of python script to be executed.")
      .defaultValue("")
      .required(true)
    descriptor = script :: descriptor
    descriptor = execFunction :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/script/python.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.ScriptGroup)
  }
  override def initialize(ctx: ProcessContext): Unit = {}

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val spark = pec.get[SparkSession]()

    val df = in.read()

    val jep = new Jep()
    val scriptPath = "/tmp/pythonExcutor-"+ UUID.randomUUID() +".py"
    FileUtil.writeFile(script,scriptPath)
    jep.runScript(scriptPath)


    val listInfo = df.toJSON.collectAsList()
    jep.eval(s"result = $execFunction($listInfo)")
    val resultArrayList = jep.getValue("result",new util.ArrayList().getClass)
    println("Execute Python Result : " + resultArrayList + "!!!!!!!!!!!!!!!!!!!!!")


    var resultList = List[Map[String, String]]()
    val it = resultArrayList.iterator()
    while(it.hasNext){
      val i = it.next().asInstanceOf[java.util.HashMap[String, Any]]
      val item =  mapAsScalaMap(i).toMap[String, Any]
      var new_item = Map[String, String]()
      item.foreach(m => {
        val key = m._1
        val value = m._2
        new_item += (key -> String.valueOf(value))
      })
      resultList =  new_item +: resultList
    }
    println("Convert Python Result to Scala List: " + resultList + "!!!!!!!!!!!!!!!!!!!!!")


    val rows = resultList.map( m => Row(m.values.toSeq:_*))
    //println("rows: " + rows + "!!!!!!!!!!!!!!!!!!!!!")
    val header = resultList.head.keys.toList
    //println("header: " + header + "!!!!!!!!!!!!!!!!!!!!!")
    val schema = StructType(header.map(fieldName => new StructField(fieldName, StringType, true)))
    println("schema: " + schema + "!!!!!!!!!!!!!!!!!!!!!")

    val rdd = spark.sparkContext.parallelize(rows)
    val resultDF = spark.createDataFrame(rdd, schema)
    resultDF.show()

    out.write(resultDF)
  }
}
