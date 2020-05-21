package cn.piflow.conf.util

import java.io.PrintWriter

import cn.piflow.conf.bean.FlowBean
import cn.piflow.util.{ConfigureUtil, PropertyUtil}
import sys.process._

object ScalaExecutorUtil {

  val userDir = System.getProperty("user.dir")
  //val scalaDir =  s"$userDir/scala"
  val scalaDir = PropertyUtil.getScalaPath()
  var packageName : String = "cn.piflow.bundle.script"
  val className : String = "ScalaFile1"
  def construct(className : String, script : String) : String = {


    val path = s"$scalaDir/$className.scala"
    val code =
      s"""
        |package $packageName
        |import org.apache.spark.sql.{DataFrame, SparkSession}
        |import org.apache.spark.sql._
        |import cn.piflow.{JobContext, JobInputStream, JobOutputStream}
        |
        |
        |object $className {
        |  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext) : Unit  ={
        |    val spark = pec.get[SparkSession]()
        |    import spark.implicits._
        |    $script
        |  }
        |}
      """.stripMargin
    val out = new PrintWriter(path)
    out.write(code)
    out.close()
    path
  }

  def buildJar(className : String, classPath : String) : String = {

    //val piflowbundle = s"$userDir/lib/piflow-server-0.9.jar"
    //val piflowbundle = "/opt/project/piflow/piflow-server/target/piflow-server-0.9.jar"
    //"-encoding UTF8"
    val piflowbundle = ConfigureUtil.getPiFlowBundlePath()
    val jarFile = s"$scalaDir/$className.jar"
    val command = s"scalac -cp $piflowbundle -d $jarFile $classPath"
    println(s"Build ScalaExecutor jar: $command")
    command.!!
    jarFile
  }

  def buildScalaExcutorJar( flowBean : FlowBean) : List[String] = {
    var scalaPluginList = List[String]()
    flowBean.stops.foreach{s => {
      if(s.bundle.equals("cn.piflow.bundle.script.ExecuteScala")){

        //val plugin = s.flowName + "_" + s.name + "_" + s.uuid
        val plugin = s.properties.getOrElse("plugin", "")
        val script = s.properties.getOrElse("script", "")
        if(!script.equals("")){
          val classFile = construct(plugin, script)
          val jarFile = buildJar(plugin, classFile)
          scalaPluginList = jarFile +: scalaPluginList
        }
      }
    }}
    scalaPluginList
  }

  def main(args: Array[String]): Unit = {
    val script =
      """
        |val df = in.read()
        |df.show()
        |val df1 = df.select("title")
        |out.write(df1)
      """.stripMargin
    val code = construct( "ScalaFile",script)
    println(code)
  }
}
